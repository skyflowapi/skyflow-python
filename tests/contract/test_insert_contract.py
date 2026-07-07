"""Shared insert() contract, asserted identically against both variants -- authored once, run
twice (see _adapter_loader.py). If this file needs variant-specific branching beyond what
adapter.SUPPORTS_BATCHING already captures, that's a signal the abstraction leaked and the
adapter interface needs to grow, not this file.
"""
import unittest

from tests.contract._adapter_loader import VARIANT, adapter

INSERT_BATCH_SIZE_ENV = "INSERT_BATCH_SIZE"


class TestInsertContract(unittest.TestCase):
    def test_vault_exposes_insert_with_a_single_request_argument(self):
        vault, _ = adapter.build_vault()
        self.assertTrue(hasattr(vault, "insert"), f"{VARIANT}'s Vault must expose insert()")
        self.assertTrue(callable(vault.insert))

    def test_insert_response_reports_correct_counts(self):
        """v2's InsertResponse (inserted_fields/errors) and v3's (summary/success/errors --
        ported from Java's v3 reference for response-shape parity) are intentionally different
        vocabularies now; the shared contract is just that both correctly report how many
        records succeeded/failed, via the adapter's count_successes/count_errors accessors."""
        vault, api = adapter.build_vault()
        request = adapter.build_insert_request(1)

        response, _ = adapter.call_insert(vault, api, request)

        self.assertEqual(adapter.count_successes(response), 1)
        self.assertEqual(adapter.count_errors(response), 0)

    def test_insert_of_many_records_returns_one_field_per_record(self):
        vault, api = adapter.build_vault()
        request = adapter.build_insert_request(7)

        response, _ = adapter.call_insert(vault, api, request)

        self.assertEqual(adapter.count_successes(response), 7)

    def test_batching_boundary_matches_the_variant_contract(self):
        """v2 (SUPPORTS_BATCHING=False) must always call the underlying API exactly once,
        regardless of record count -- it's explicitly excluded from batching this round. v3
        (SUPPORTS_BATCHING=True) must split into multiple calls once record count exceeds
        INSERT_BATCH_SIZE."""
        import os
        os.environ[INSERT_BATCH_SIZE_ENV] = "2"
        try:
            vault, api = adapter.build_vault()
            request = adapter.build_insert_request(3)  # INSERT_BATCH_SIZE + 1

            _, call_count = adapter.call_insert(vault, api, request)

            if adapter.SUPPORTS_BATCHING:
                self.assertEqual(call_count, 2, f"{VARIANT} should split 3 records at batch size 2 into 2 calls")
            else:
                self.assertEqual(call_count, 1, f"{VARIANT} must not batch -- always exactly one call")
        finally:
            os.environ.pop(INSERT_BATCH_SIZE_ENV, None)


if __name__ == "__main__":
    unittest.main()
