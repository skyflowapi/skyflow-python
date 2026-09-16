"""Shared insert() contract, asserted identically against both variants -- authored once, run
twice (see _adapter_loader.py). If this file needs variant-specific branching, that's a signal
the abstraction leaked and the adapter interface needs to grow, not this file.
"""
import unittest

from tests.contract._adapter_loader import VARIANT, adapter


class TestInsertContract(unittest.TestCase):
    def test_vault_exposes_insert_with_a_single_request_argument(self):
        vault, _ = adapter.build_vault()
        self.assertTrue(hasattr(vault, "insert"), f"{VARIANT}'s Vault must expose insert()")
        self.assertTrue(callable(vault.insert))

    def test_insert_response_reports_correct_counts(self):
        """v2 and v3 now share the exact same InsertResponse shape (inserted_fields/errors,
        each entry tagged request_index); the contract accesses it via the adapter's
        count_successes/count_errors functions rather than assuming the shape directly."""
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

    def test_insert_always_makes_exactly_one_api_call_regardless_of_record_count(self):
        """Neither variant batches -- every insert(), no matter how many records, must reach
        the underlying API exactly once."""
        vault, api = adapter.build_vault()
        request = adapter.build_insert_request(3)

        _, call_count = adapter.call_insert(vault, api, request)

        self.assertEqual(call_count, 1, f"{VARIANT} must always call the underlying API exactly once")


if __name__ == "__main__":
    unittest.main()
