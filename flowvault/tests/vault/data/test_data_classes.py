import unittest

from common.vault.data import BaseInsertRequest, BaseInsertResponse
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import InsertRequest, InsertResponse, Upsert


class TestInsertRequest(unittest.TestCase):
    def test_is_a_base_insert_request(self):
        request = InsertRequest(records=[{"values": {"a": 1}}], table="t1")
        self.assertIsInstance(request, BaseInsertRequest)
        self.assertEqual(request.table, "t1")

    def test_records_are_plain_dicts_supporting_per_record_overrides(self):
        upsert = Upsert(update_type=UpsertType.REPLACE, unique_columns=["a"])
        record = {"values": {"a": 1}, "table": "t2", "upsert": upsert}
        request = InsertRequest(records=[record])
        self.assertEqual(request.records[0]["values"], {"a": 1})
        self.assertEqual(request.records[0]["table"], "t2")
        self.assertIs(request.records[0]["upsert"], upsert)

    def test_table_and_upsert_are_optional_defaults(self):
        request = InsertRequest(records=[{"values": {"a": 1}}])
        self.assertIsNone(request.table)
        self.assertIsNone(request.upsert)

    def test_no_v2_only_fields_exist(self):
        request = InsertRequest(records=[{"values": {"a": 1}}])
        for legacy_field in ("values", "homogeneous", "continue_on_error", "token_mode", "return_tokens"):
            self.assertFalse(hasattr(request, legacy_field), f"v3 InsertRequest should not have '{legacy_field}'")


class TestUpsert(unittest.TestCase):
    def test_construction(self):
        upsert = Upsert(update_type=UpsertType.UPDATE, unique_columns=["email"])
        self.assertEqual(upsert.update_type, UpsertType.UPDATE)
        self.assertEqual(upsert.unique_columns, ["email"])


class TestInsertResponse(unittest.TestCase):
    """Shared shape with PDB's InsertResponse -- inserted_fields/errors, each entry tagged
    request_index -- plain dicts/list-of-dicts, not custom classes."""

    def test_shape(self):
        inserted_fields = [{"request_index": 0, "skyflow_id": "id1"}]
        response = InsertResponse(inserted_fields=inserted_fields, errors=[])

        self.assertIs(response.inserted_fields, inserted_fields)
        self.assertEqual(response.errors, [])

    def test_is_a_base_insert_response(self):
        response = InsertResponse(inserted_fields=[], errors=None)
        self.assertIsInstance(response, BaseInsertResponse)

    def test_repr_does_not_raise(self):
        response = InsertResponse(
            inserted_fields=[],
            errors=[{"request_index": 0, "error": "boom", "code": 500, "request_id": None}],
        )
        self.assertIn("InsertResponse", repr(response))


if __name__ == "__main__":
    unittest.main()
