import unittest

from common.vault.data import BaseInsertRequest, BaseInsertResponse
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import (
    InsertRequest,
    InsertResponse,
    GetRequest,
    GetResponse,
    UpdateRequest,
    UpdateResponse,
    DeleteRequest,
    DeleteResponse,
    DetokenizeRequest,
    DetokenizeResponse,
    TokenizeRequest,
    TokenizeResponse,
)


class TestInsertRequest(unittest.TestCase):
    def test_is_a_base_insert_request(self):
        request = InsertRequest(values=[{"values": {"a": 1}}], table="t1")
        self.assertIsInstance(request, BaseInsertRequest)
        self.assertEqual(request.table, "t1")

    def test_records_are_plain_dicts_supporting_per_record_overrides(self):
        upsert = {"update_type": UpsertType.REPLACE, "unique_columns": ["a"]}
        record = {"values": {"a": 1}, "table": "t2", "upsert": upsert}
        request = InsertRequest(values=[record])
        self.assertEqual(request.values[0]["values"], {"a": 1})
        self.assertEqual(request.values[0]["table"], "t2")
        self.assertIs(request.values[0]["upsert"], upsert)

    def test_table_and_upsert_are_optional_defaults(self):
        request = InsertRequest(values=[{"values": {"a": 1}}])
        self.assertIsNone(request.table)
        self.assertIsNone(request.upsert)

    def test_no_v2_only_fields_exist(self):
        request = InsertRequest(values=[{"values": {"a": 1}}])
        for legacy_field in ("tokens", "homogeneous", "continue_on_error", "token_mode", "return_tokens"):
            self.assertFalse(hasattr(request, legacy_field), f"v3 InsertRequest should not have '{legacy_field}'")


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


class TestGetRequest(unittest.TestCase):
    def test_required_and_optional_defaults(self):
        request = GetRequest(table="t1", ids=["id1"])
        self.assertEqual(request.table, "t1")
        self.assertEqual(request.ids, ["id1"])
        self.assertIsNone(request.unique_values)
        self.assertIsNone(request.columns)
        self.assertIsNone(request.column_redactions)
        self.assertIsNone(request.limit)
        self.assertIsNone(request.offset)

    def test_all_fields_stored(self):
        request = GetRequest(
            table="t1", ids=["id1"], unique_values=[{"email": "a@b.com"}], columns=["a", "b"],
            column_redactions=[{"column_name": "a", "redaction": "mask1"}], limit=10, offset=5,
        )
        self.assertEqual(request.unique_values, [{"email": "a@b.com"}])
        self.assertEqual(request.columns, ["a", "b"])
        self.assertEqual(request.column_redactions, [{"column_name": "a", "redaction": "mask1"}])
        self.assertEqual(request.limit, 10)
        self.assertEqual(request.offset, 5)


class TestGetResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"request_index": 0, "skyflow_id": "id1", "data": {"a": 1}}]
        response = GetResponse(records=records, errors=[])
        self.assertIs(response.records, records)
        self.assertEqual(response.errors, [])

    def test_defaults(self):
        response = GetResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.errors)

    def test_repr_and_str_do_not_raise(self):
        response = GetResponse(records=[], errors=[{"request_index": 0, "error": "boom"}])
        self.assertIn("GetResponse", repr(response))
        self.assertIn("GetResponse", str(response))


class TestUpdateRequest(unittest.TestCase):
    def test_required_and_optional_defaults(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "values": {"a": 1}}])
        self.assertEqual(request.records, [{"skyflow_id": "id1", "values": {"a": 1}}])
        self.assertIsNone(request.table)
        self.assertIsNone(request.update_type)

    def test_all_fields_stored(self):
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "values": {"a": 1}, "tokens": {"a": "tok"}, "table": "t2"}],
            table="t1", update_type=UpsertType.REPLACE,
        )
        self.assertEqual(request.table, "t1")
        self.assertEqual(request.update_type, UpsertType.REPLACE)
        self.assertEqual(request.records[0]["tokens"], {"a": "tok"})


class TestUpdateResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"request_index": 0, "skyflow_id": "id1"}]
        response = UpdateResponse(records=records, errors=[])
        self.assertIs(response.records, records)
        self.assertEqual(response.errors, [])

    def test_defaults(self):
        response = UpdateResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.errors)

    def test_repr_and_str_do_not_raise(self):
        response = UpdateResponse(records=[], errors=[{"request_index": 0, "error": "boom"}])
        self.assertIn("UpdateResponse", repr(response))
        self.assertIn("UpdateResponse", str(response))


class TestDeleteRequest(unittest.TestCase):
    def test_required_and_optional_defaults(self):
        request = DeleteRequest(table="t1", ids=["id1"])
        self.assertEqual(request.table, "t1")
        self.assertEqual(request.ids, ["id1"])
        self.assertIsNone(request.unique_values)

    def test_unique_values_stored(self):
        request = DeleteRequest(table="t1", unique_values=[{"email": "a@b.com"}])
        self.assertEqual(request.unique_values, [{"email": "a@b.com"}])


class TestDeleteResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"request_index": 0, "skyflow_id": "id1"}]
        response = DeleteResponse(records=records, errors=[])
        self.assertIs(response.records, records)
        self.assertEqual(response.errors, [])

    def test_defaults(self):
        response = DeleteResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.errors)

    def test_repr_and_str_do_not_raise(self):
        response = DeleteResponse(records=[], errors=[{"request_index": 0, "error": "boom"}])
        self.assertIn("DeleteResponse", repr(response))
        self.assertIn("DeleteResponse", str(response))


class TestDetokenizeRequest(unittest.TestCase):
    def test_required_and_optional_defaults(self):
        request = DetokenizeRequest(tokens=["tok1", "tok2"])
        self.assertEqual(request.tokens, ["tok1", "tok2"])
        self.assertIsNone(request.token_group_redactions)

    def test_token_group_redactions_stored(self):
        request = DetokenizeRequest(
            tokens=["tok1"], token_group_redactions=[{"token_group_name": "g1", "redaction": "mask1"}],
        )
        self.assertEqual(request.token_group_redactions, [{"token_group_name": "g1", "redaction": "mask1"}])


class TestDetokenizeResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"request_index": 0, "token": "tok1", "value": "john"}]
        response = DetokenizeResponse(records=records, errors=[])
        self.assertIs(response.records, records)
        self.assertEqual(response.errors, [])

    def test_defaults(self):
        response = DetokenizeResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.errors)

    def test_repr_and_str_do_not_raise(self):
        response = DetokenizeResponse(records=[], errors=[{"request_index": 0, "error": "boom"}])
        self.assertIn("DetokenizeResponse", repr(response))
        self.assertIn("DetokenizeResponse", str(response))


class TestTokenizeRequest(unittest.TestCase):
    def test_values_stored(self):
        values = [{"value": "a@b.com", "token_group_names": ["g1"]}]
        request = TokenizeRequest(values=values)
        self.assertEqual(request.values, values)


class TestTokenizeResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"request_index": 0, "token": "tok1", "token_group_name": "g1"}]
        response = TokenizeResponse(records=records, errors=[])
        self.assertIs(response.records, records)
        self.assertEqual(response.errors, [])

    def test_defaults(self):
        response = TokenizeResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.errors)

    def test_repr_and_str_do_not_raise(self):
        response = TokenizeResponse(records=[], errors=[{"request_index": 0, "error": "boom"}])
        self.assertIn("TokenizeResponse", repr(response))
        self.assertIn("TokenizeResponse", str(response))


if __name__ == "__main__":
    unittest.main()
