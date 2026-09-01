import unittest

from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import (
    UpsertOptions,
    ColumnRedaction,
    InsertRequestRecord,
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
    QueryRequest,
    QueryResponse,
    GetRecordRequest,
    BulkInsertRecord,
    BulkInsertRequest,
    BulkInsertResponse,
    BulkSummary,
    BulkDetokenizeRequest,
    BulkDetokenizeResponse,
    DetokenizeSummary,
)


class TestInsertRequest(unittest.TestCase):
    def test_records_and_table_stored(self):
        records = [InsertRequestRecord(data={"a": 1})]
        request = InsertRequest(records=records, table_name="t1")
        self.assertIs(request.records, records)
        self.assertEqual(request.table_name, "t1")

    def test_record_fields_and_per_record_overrides(self):
        upsert = UpsertOptions(update_type=UpsertType.REPLACE, unique_columns=["a"])
        record = InsertRequestRecord(data={"a": 1}, table_name="t2", tokens={"a": "tok"}, upsert=upsert)
        request = InsertRequest(records=[record])
        self.assertEqual(request.records[0].data, {"a": 1})
        self.assertEqual(request.records[0].table_name, "t2")
        self.assertEqual(request.records[0].tokens, {"a": "tok"})
        self.assertIs(request.records[0].upsert, upsert)

    def test_table_and_upsert_are_optional_defaults(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})])
        self.assertIsNone(request.table_name)
        self.assertIsNone(request.upsert)

    def test_record_optional_defaults(self):
        record = InsertRequestRecord(data={"a": 1})
        self.assertIsNone(record.table_name)
        self.assertIsNone(record.tokens)
        self.assertIsNone(record.upsert)


class TestUpsertOptions(unittest.TestCase):
    def test_fields_stored(self):
        opts = UpsertOptions(unique_columns=["email"], update_type=UpsertType.UPDATE)
        self.assertEqual(opts.unique_columns, ["email"])
        self.assertEqual(opts.update_type, UpsertType.UPDATE)

    def test_update_type_optional(self):
        opts = UpsertOptions(unique_columns=["email"])
        self.assertIsNone(opts.update_type)


class TestColumnRedaction(unittest.TestCase):
    def test_fields_stored(self):
        cr = ColumnRedaction(column_name="email", redaction="MASKED")
        self.assertEqual(cr.column_name, "email")
        self.assertEqual(cr.redaction, "MASKED")


class TestInsertResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"skyflow_id": "id1", "http_code": 200, "error": None}]
        response = InsertResponse(records=records)
        self.assertIs(response.records, records)

    def test_defaults(self):
        response = InsertResponse()
        self.assertIsNone(response.records)

    def test_repr_does_not_raise(self):
        response = InsertResponse(records=[{"skyflow_id": "id1"}])
        self.assertIn("InsertResponse", repr(response))
        self.assertIn("InsertResponse", str(response))


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
            column_redactions=[ColumnRedaction(column_name="a", redaction="mask1")], limit=10, offset=5,
        )
        self.assertEqual(request.unique_values, [{"email": "a@b.com"}])
        self.assertEqual(request.columns, ["a", "b"])
        self.assertEqual(request.column_redactions[0].column_name, "a")
        self.assertEqual(request.column_redactions[0].redaction, "mask1")
        self.assertEqual(request.limit, 10)
        self.assertEqual(request.offset, 5)


class TestGetResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"skyflow_id": "id1", "data": {"a": 1}, "http_code": 200}]
        response = GetResponse(records=records)
        self.assertIs(response.records, records)

    def test_defaults(self):
        response = GetResponse()
        self.assertIsNone(response.records)

    def test_repr_and_str_do_not_raise(self):
        response = GetResponse(records=[])
        self.assertIn("GetResponse", repr(response))
        self.assertIn("GetResponse", str(response))


class TestUpdateRequest(unittest.TestCase):
    def test_required_and_optional_defaults(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}}])
        self.assertEqual(request.records, [{"skyflow_id": "id1", "data": {"a": 1}}])
        self.assertIsNone(request.table_name)
        self.assertIsNone(request.update_type)

    def test_all_fields_stored(self):
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}, "tokens": {"a": "tok"}, "table_name": "t2"}],
            table_name="t1", update_type=UpsertType.REPLACE,
        )
        self.assertEqual(request.table_name, "t1")
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
        records = [{"skyflow_id": "id1", "http_code": 200, "error": None}]
        response = DeleteResponse(records=records)
        self.assertIs(response.records, records)

    def test_defaults(self):
        response = DeleteResponse()
        self.assertIsNone(response.records)

    def test_repr_and_str_do_not_raise(self):
        response = DeleteResponse(records=[])
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
        records = [{"token": "tok1", "value": "john", "http_code": 200, "error": None}]
        response = DetokenizeResponse(records=records)
        self.assertIs(response.records, records)

    def test_defaults(self):
        response = DetokenizeResponse()
        self.assertIsNone(response.records)

    def test_repr_and_str_do_not_raise(self):
        response = DetokenizeResponse(records=[])
        self.assertIn("DetokenizeResponse", repr(response))
        self.assertIn("DetokenizeResponse", str(response))


class TestQueryRequest(unittest.TestCase):
    def test_query_stored(self):
        request = QueryRequest(query="SELECT * FROM t1")
        self.assertEqual(request.query, "SELECT * FROM t1")


class TestQueryResponse(unittest.TestCase):
    def test_shape(self):
        records = [{"data": {"a": 1}}]
        response = QueryResponse(records=records, metadata={"columns": ["a"]})
        self.assertIs(response.records, records)
        self.assertEqual(response.metadata, {"columns": ["a"]})

    def test_defaults(self):
        response = QueryResponse()
        self.assertIsNone(response.records)
        self.assertIsNone(response.metadata)

    def test_repr_and_str_do_not_raise(self):
        response = QueryResponse(records=[], metadata=None)
        self.assertIn("QueryResponse", repr(response))
        self.assertIn("QueryResponse", str(response))


class TestGetRecordRequest(unittest.TestCase):
    def test_fields_stored(self):
        record = GetRecordRequest(table="t1", ids=["id1"], columns=["a"],
                                  column_redactions=[ColumnRedaction(column_name="a", redaction="MASKED")],
                                  unique_values=[{"email": "a@b.com"}])
        self.assertEqual(record.table, "t1")
        self.assertEqual(record.ids, ["id1"])
        self.assertEqual(record.columns, ["a"])
        self.assertEqual(record.column_redactions[0].column_name, "a")
        self.assertEqual(record.column_redactions[0].redaction, "MASKED")
        self.assertEqual(record.unique_values, [{"email": "a@b.com"}])

    def test_optional_defaults(self):
        record = GetRecordRequest(table="t1")
        self.assertIsNone(record.ids)
        self.assertIsNone(record.columns)
        self.assertIsNone(record.column_redactions)
        self.assertIsNone(record.unique_values)


class TestBulkInsertRecord(unittest.TestCase):
    def test_fields_stored(self):
        record = BulkInsertRecord(data={"a": 1}, table="t1", upsert=UpsertOptions(unique_columns=["a"]))
        self.assertEqual(record.data, {"a": 1})
        self.assertEqual(record.table, "t1")
        self.assertEqual(record.upsert.unique_columns, ["a"])

    def test_optional_defaults(self):
        record = BulkInsertRecord(data={"a": 1})
        self.assertIsNone(record.table)
        self.assertIsNone(record.upsert)


class TestBulkInsertRequest(unittest.TestCase):
    def test_fields_stored(self):
        records = [BulkInsertRecord(data={"a": 1})]
        request = BulkInsertRequest(records=records, table="t1")
        self.assertIs(request.records, records)
        self.assertEqual(request.table, "t1")
        self.assertIsNone(request.upsert)


class TestBulkSummary(unittest.TestCase):
    def test_fields_and_repr(self):
        summary = BulkSummary(total_records=3, total_inserted=2, total_failed=1)
        self.assertEqual((summary.total_records, summary.total_inserted, summary.total_failed), (3, 2, 1))
        self.assertIn("BulkSummary", repr(summary))


class TestBulkInsertResponse(unittest.TestCase):
    def test_records_to_retry_only_server_5xx_except_529(self):
        records = [
            {"index": 0, "http_code": 200},
            {"index": 1, "http_code": 500},
            {"index": 2, "http_code": 529},
            {"index": 3, "http_code": 400},
            {"index": 4, "http_code": 503},
        ]
        originals = ["r0", "r1", "r2", "r3", "r4"]
        response = BulkInsertResponse(summary=None, records=records, _original_records=originals)
        self.assertEqual(response.records_to_retry(), ["r1", "r4"])

    def test_records_to_retry_empty_without_originals(self):
        response = BulkInsertResponse(summary=None, records=[{"index": 0, "http_code": 500}])
        self.assertEqual(response.records_to_retry(), [])

    def test_repr_does_not_raise(self):
        self.assertIn("BulkInsertResponse", repr(BulkInsertResponse(summary=BulkSummary(), records=[])))


class TestBulkDetokenizeRequest(unittest.TestCase):
    def test_fields_stored(self):
        request = BulkDetokenizeRequest(tokens=["t1", "t2"], token_group_redactions=[{"token_group_name": "g", "redaction": "MASKED"}])
        self.assertEqual(request.tokens, ["t1", "t2"])
        self.assertEqual(request.token_group_redactions, [{"token_group_name": "g", "redaction": "MASKED"}])


class TestDetokenizeSummary(unittest.TestCase):
    def test_fields_and_repr(self):
        summary = DetokenizeSummary(total_tokens=2, total_detokenized=1, total_failed=1)
        self.assertEqual((summary.total_tokens, summary.total_detokenized, summary.total_failed), (2, 1, 1))
        self.assertIn("DetokenizeSummary", repr(summary))


class TestBulkDetokenizeResponse(unittest.TestCase):
    def test_tokens_to_retry_only_server_5xx_except_529(self):
        records = [
            {"index": 0, "http_code": 200},
            {"index": 1, "http_code": 500},
            {"index": 2, "http_code": 529},
        ]
        response = BulkDetokenizeResponse(summary=None, records=records, _original_tokens=["a", "b", "c"])
        self.assertEqual(response.tokens_to_retry(), ["b"])

    def test_repr_does_not_raise(self):
        self.assertIn("BulkDetokenizeResponse", repr(BulkDetokenizeResponse(summary=DetokenizeSummary(), records=[])))


if __name__ == "__main__":
    unittest.main()
