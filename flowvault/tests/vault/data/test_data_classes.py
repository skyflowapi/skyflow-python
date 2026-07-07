import unittest

from common.vault.data import BaseInsertRequest
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import InsertRecord, InsertRequest, InsertResponse, Upsert


class TestInsertRecord(unittest.TestCase):
    def test_defaults(self):
        record = InsertRecord(data={"a": 1})
        self.assertEqual(record.data, {"a": 1})
        self.assertIsNone(record.table)
        self.assertIsNone(record.upsert)

    def test_per_record_overrides(self):
        upsert = Upsert(update_type=UpsertType.REPLACE, unique_columns=["a"])
        record = InsertRecord(data={"a": 1}, table="t2", upsert=upsert)
        self.assertEqual(record.table, "t2")
        self.assertIs(record.upsert, upsert)


class TestInsertRequest(unittest.TestCase):
    def test_is_a_base_insert_request(self):
        request = InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1")
        self.assertIsInstance(request, BaseInsertRequest)
        self.assertEqual(request.table, "t1")

    def test_table_and_upsert_are_optional_defaults(self):
        request = InsertRequest(records=[InsertRecord(data={"a": 1})])
        self.assertIsNone(request.table)
        self.assertIsNone(request.upsert)

    def test_no_v2_only_fields_exist(self):
        request = InsertRequest(records=[InsertRecord(data={"a": 1})])
        for legacy_field in ("values", "homogeneous", "continue_on_error", "token_mode", "return_tokens"):
            self.assertFalse(hasattr(request, legacy_field), f"v3 InsertRequest should not have '{legacy_field}'")


class TestUpsert(unittest.TestCase):
    def test_construction(self):
        upsert = Upsert(update_type=UpsertType.UPDATE, unique_columns=["email"])
        self.assertEqual(upsert.update_type, UpsertType.UPDATE)
        self.assertEqual(upsert.unique_columns, ["email"])


class TestInsertResponse(unittest.TestCase):
    def test_mirrors_java_summary_success_errors_shape(self):
        """Java parity for the overall shape (summary + per-record success/errors, each entry
        tagged with its index in the original request) -- but summary/success/errors are plain
        dicts/list-of-dicts here, not custom classes, by explicit choice."""
        summary = {"total_records": 1, "total_inserted": 1, "total_failed": 0}
        success = [{"index": 0, "skyflow_id": "id1"}]
        response = InsertResponse(summary=summary, success=success, errors=[])

        self.assertIs(response.summary, summary)
        self.assertEqual(response.success, success)
        self.assertEqual(response.errors, [])

    def test_repr_does_not_raise(self):
        response = InsertResponse(
            summary={"total_records": 1, "total_inserted": 0, "total_failed": 1},
            success=[],
            errors=[{"index": 0, "error": "boom", "code": 500, "request_id": None}],
        )
        self.assertIn("InsertResponse", repr(response))


if __name__ == "__main__":
    unittest.main()
