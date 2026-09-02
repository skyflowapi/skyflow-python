import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.vault.controller import VaultController
from skyflow_flowvault.vault.data import (
    UpsertOptions,
    ColumnRedaction,
    InsertRequestRecord,
    InsertRequest,
    GetRequest,
    GetRecordRequest,
    UpdateRequest,
    DeleteRequest,
    DetokenizeRequest,
    QueryRequest,
    BulkInsertRequestRecord,
    BulkInsertRequest,
    BulkDetokenizeRequest,
    BulkInsertOptions,
    BulkDetokenizeOptions,
)
from skyflow_flowvault.utils.enums import UpsertType, CustomHeaderKey


class FakeExecuteQueryRecord:
    def __init__(self, data=None):
        self.data = data


class FakeRecordResponseObject:
    def __init__(self, skyflow_id=None, tokens=None, data=None, hashed_data=None, error=None, http_code=None, table_name=None):
        self.skyflow_id = skyflow_id
        self.tokens = tokens
        self.data = data
        self.hashed_data = hashed_data
        self.error = error
        self.http_code = http_code
        self.table_name = table_name


class FakeDeleteResponseObject:
    def __init__(self, skyflow_id=None, error=None, http_code=None):
        self.skyflow_id = skyflow_id
        self.error = error
        self.http_code = http_code


class FakeDetokenizeResponseObject:
    def __init__(self, token=None, value=None, token_group_name=None, error=None, http_code=None, metadata=None):
        self.token = token
        self.value = value
        self.token_group_name = token_group_name
        self.error = error
        self.http_code = http_code
        self.metadata = metadata


class FakeV1InsertResponse:
    def __init__(self, records):
        self.records = records


class FakeRawResponse:
    """Stands in for the HttpResponse wrapper returned by with_raw_response.insert_records(...) --
    exposes .data (the parsed V1InsertResponse) and .headers, mirroring the real generated
    client's RawFlowserviceClient."""

    def __init__(self, records, headers=None):
        self.data = FakeV1InsertResponse(records)
        self.headers = headers or {}


class TestVault(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.insert_api = MagicMock()
        self.vault_client.get_records_api.return_value = self.insert_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_insert_request")
    def test_insert_validates_before_initializing_client(self, mock_validate):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1")

        self.vault.insert(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_insert_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[], table_name="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # shared BaseVaultController validation helpers, exercised end-to-end via insert()
    # (unit-tested in isolation in common/tests/vault/test_base_vault_controller.py)
    # ------------------------------------------------------------------ #

    def test_insert_raises_on_empty_key(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"": "value"})], table_name="t1"))
        self.insert_api.with_raw_response.insert_records.assert_not_called()

    def test_insert_allows_empty_value(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": ""})], table_name="t1"))
        self.insert_api.with_raw_response.insert_records.assert_called_once()

    def test_insert_raises_on_non_dict_values(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data=["not", "a", "dict"])], table_name="t1"))

    def test_insert_raises_on_empty_values_dict(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={})], table_name="t1"))

    def test_insert_raises_on_invalid_request_level_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="   "))

    def test_insert_raises_on_invalid_per_record_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1}, table_name="   ")]))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table_and_upsert(self):
        """When no record sets its own table/upsert, both go ONLY at the request level -- the
        vault rejects sending table_name/upsert in both places (see the validation tests), so
        the wire records must NOT also carry a resolved copy."""
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1})],
            table_name="t1",
            upsert=UpsertOptions(update_type= UpsertType.REPLACE, unique_columns= ["a"]),
        )

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(len(kwargs["records"]), 1)
        self.assertEqual(kwargs["records"][0].data, {"a": 1})
        self.assertIsNone(kwargs["records"][0].table_name)  # NOT resolved onto the record
        self.assertEqual(kwargs["upsert"].update_type, "REPLACE")
        self.assertEqual(kwargs["upsert"].unique_columns, ["a"])

    def test_setting_table_at_both_request_and_record_level_raises(self):
        """The vault rejects table_name in both places at once -- confirmed directly against a
        real vault. validate_insert_request (tested separately) is what actually raises this;
        this test just confirms insert() surfaces it rather than silently choosing one."""
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, table_name="t2")],
            table_name="t1",
        )

        with self.assertRaises(SkyflowError):
            self.vault.insert(request)
        self.insert_api.with_raw_response.insert_records.assert_not_called()

    def test_per_record_table_and_upsert_used_when_request_level_unset(self):
        """Legitimate per-record use: no request-level table/upsert at all -- Java parity
        requires EVERY record to set its own table in this mode (see validation tests), so both
        records do; only the second also sets its own upsert."""
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(records=[
            InsertRequestRecord(data={"a": 1}, table_name="t2", upsert=UpsertOptions(unique_columns= ["b"])),
            InsertRequestRecord(data={"a": 2}, table_name="t2"),
        ])

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertIsNone(kwargs["table_name"])
        self.assertNotIn("upsert", kwargs)
        self.assertEqual(kwargs["records"][0].table_name, "t2")
        self.assertEqual(kwargs["records"][0].upsert.unique_columns, ["b"])
        self.assertEqual(kwargs["records"][1].table_name, "t2")
        self.assertIsNone(kwargs["records"][1].upsert)

    def test_no_request_level_table_passed_as_none(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}, table_name="t2")])  # no request-level table

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertIsNone(kwargs["table_name"])

    def test_wire_shape_matches_confirmed_working_request(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(records=[
            InsertRequestRecord(
                data={"name": "saileshwar", "email": "nanana@gmail.com"},
                table_name="table1",
                upsert=UpsertOptions(update_type= UpsertType.UPDATE, unique_columns= ["email"]),
            ),
        ])

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertIsNone(kwargs["table_name"])
        self.assertNotIn("upsert", kwargs)
        self.assertEqual(kwargs["records"][0].table_name, "table1")
        self.assertEqual(kwargs["records"][0].upsert.update_type, "UPDATE")
        self.assertEqual(kwargs["records"][0].upsert.unique_columns, ["email"])

    def test_no_upsert_is_omitted_not_sent_as_none(self):
        """upsert must be OMITTED from the wire call entirely when unset, not passed as None --
        a real vault confirmed a working request never includes a null upsert/tableName key."""
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1")

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertNotIn("upsert", kwargs)
        self.assertIsNone(kwargs["records"][0].upsert)

    # ------------------------------------------------------------------ #
    # response shape -- unified records list (FlowDB contract), tokens normalized
    # ------------------------------------------------------------------ #

    def test_successful_record_carries_normalized_fields(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string", "path": "p"}]},
                data={"name": "john doe"},
                hashed_data={"name": [{"data": "h", "hashName": "hash1"}]},
                table_name="table1",
                http_code=200,
            ),
        ], headers={"x-request-id": "req-1"})
        response = self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"name": "john doe"})], table_name="table1"))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["table_name"], "table1")
        self.assertEqual(record["tokens"], {"name": [{"token": "tok1", "token_group_name": "deterministic_string", "path": "p"}]})
        self.assertNotIn("data", record)  # insert response omits data
        self.assertEqual(record["hashed_data"], {"name": [{"data": "h", "hash_name": "hash1"}]})
        self.assertEqual(record["http_code"], 200)
        self.assertIsNone(record["error"])

    def test_tokens_normalized_to_typed_list_per_group(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"email": [
                    {"token": "tok-det", "tokenGroupName": "deterministic_string"},
                    {"token": "tok-nondet", "tokenGroupName": "nondeterministic_string"},
                ]},
            ),
        ])
        response = self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"email": "a@b.com"})], table_name="t1"))

        self.assertEqual(response.records[0]["tokens"]["email"], [
            {"token": "tok-det", "token_group_name": "deterministic_string", "path": None},
            {"token": "tok-nondet", "token_group_name": "nondeterministic_string", "path": None},
        ])

    def test_success_and_error_records_in_one_list(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([
            FakeRecordResponseObject(skyflow_id="id1", tokens=None, http_code=200),
            FakeRecordResponseObject(error="bad row", http_code=400, table_name="t1"),
        ], headers={"x-request-id": "req-2"})
        response = self.vault.insert(InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}), InsertRequestRecord(data={"a": 2})], table_name="t1",
        ))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0]["skyflow_id"], "id1")
        self.assertIsNone(response.records[0]["error"])
        self.assertEqual(response.records[1]["error"], "bad row")
        self.assertEqual(response.records[1]["http_code"], 400)
        self.assertIsNone(response.records[1]["skyflow_id"])

    # ------------------------------------------------------------------ #
    # no batching -- every insert is exactly one API call
    # ------------------------------------------------------------------ #

    def test_all_records_sent_in_a_single_api_call_regardless_of_count(self):
        self.insert_api.with_raw_response.insert_records.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [InsertRequestRecord(data={"a": i}) for i in range(4)]

        response = self.vault.insert(InsertRequest(records=records, table_name="t1"))

        self.insert_api.with_raw_response.insert_records.assert_called_once()
        call_size = len(self.insert_api.with_raw_response.insert_records.call_args.kwargs["records"])
        self.assertEqual(call_size, 4)
        self.assertEqual(len(response.records), 4)
        self.assertEqual([r["skyflow_id"] for r in response.records], ["id-0", "id-1", "id-2", "id-3"])

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_record_as_an_error(self):
        """Without batching, one API call carries every record -- a transport-level exception
        on that single call means every record in the request fails, not just some."""
        self.insert_api.with_raw_response.insert_records.side_effect = Exception("network blip")
        records = [InsertRequestRecord(data={"a": 1}), InsertRequestRecord(data={"a": 2})]

        response = self.vault.insert(InsertRequest(records=records, table_name="t1"))

        self.insert_api.with_raw_response.insert_records.assert_called_once()
        self.assertEqual(len(response.records), 2)
        self.assertTrue(all("network blip" in r["error"] for r in response.records))
        self.assertTrue(all(r["skyflow_id"] is None for r in response.records))

    def test_api_error_with_structured_per_record_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=400,
            headers={"x-request-id": "req-3"},
            body={"records": [
                {"error": "Column passport has the notNull attribute, and input contains a null value.",
                 "httpCode": 400},
            ]},
        )
        self.insert_api.with_raw_response.insert_records.side_effect = api_error

        response = self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"name": "a"})], table_name="t1"))

        self.assertEqual(len(response.records), 1)
        self.assertIn("notNull", response.records[0]["error"])
        self.assertEqual(response.records[0]["http_code"], 400)

    def test_api_error_with_flat_body_falls_back_to_one_error_per_record(self):
        api_error = ApiError(status_code=500, headers={}, body={"error": "internal error"})
        self.insert_api.with_raw_response.insert_records.side_effect = api_error

        response = self.vault.insert(InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}), InsertRequestRecord(data={"a": 2})], table_name="t1",
        ))

        self.assertEqual(len(response.records), 2)
        self.assertTrue(all(r["error"] == "internal error" for r in response.records))
        self.assertTrue(all(r["http_code"] == 500 for r in response.records))

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")

    def test_no_authorization_header_when_no_token_available(self):
        self.vault_client.get_current_bearer_token.return_value = None
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertNotIn("Authorization", headers)


def fake_get_raw_response(records, headers=None):
    return SimpleNamespace(data=SimpleNamespace(records=records), headers=headers or {})


class TestVaultGet(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.get_api = MagicMock()
        self.vault_client.get_records_api.return_value = self.get_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_get_request")
    def test_get_validates_before_initializing_client(self, mock_validate):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])
        request = GetRequest(table_name="t1", ids=["id1"])

        self.vault.get(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_get_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table_name="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_get_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table_name="   ", ids=["id1"]))
        self.get_api.with_raw_response.get_records.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_table_and_ids(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", ids=["id1", "id2"]))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(kwargs["skyflow_i_ds"], ["id1", "id2"])

    def test_maps_unique_values(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", unique_values=[{"email": "a@b.com"}]))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertEqual(len(kwargs["unique_values"]), 1)
        self.assertEqual(kwargs["unique_values"][0].data, {"email": "a@b.com"})

    def test_multi_table_mode_sends_records_and_omits_single_table_fields(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(records=[
            GetRecordRequest(table_name="persons", ids=["id1"], columns=["name"]),
            GetRecordRequest(table_name="cards", unique_values=[{"email": "a@b.com"}]),
        ]))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertNotIn("table_name", kwargs)
        self.assertNotIn("skyflow_i_ds", kwargs)
        self.assertEqual(len(kwargs["records"]), 2)
        self.assertEqual(kwargs["records"][0].table_name, "persons")
        self.assertEqual(kwargs["records"][0].skyflow_i_ds, ["id1"])
        self.assertEqual(kwargs["records"][0].columns, ["name"])
        self.assertEqual(kwargs["records"][1].table_name, "cards")
        self.assertEqual(kwargs["records"][1].skyflow_i_ds, [])
        self.assertEqual(kwargs["records"][1].unique_values[0].data, {"email": "a@b.com"})

    def test_maps_column_redactions(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(
            table_name="t1", ids=["id1"], column_redactions=[ColumnRedaction(column_name="ssn", redaction="mask1")],
        ))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertEqual(len(kwargs["column_redactions"]), 1)
        self.assertEqual(kwargs["column_redactions"][0].column_name, "ssn")
        self.assertEqual(kwargs["column_redactions"][0].redaction, "mask1")

    def test_maps_limit_offset_columns(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", ids=["id1"], columns=["a", "b"], limit=10, offset=5))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertEqual(kwargs["columns"], ["a", "b"])
        self.assertEqual(kwargs["limit"], 10)
        self.assertEqual(kwargs["offset"], 5)

    # ------------------------------------------------------------------ #
    # response shape -- includes data, unlike insert
    # ------------------------------------------------------------------ #

    def test_successful_record_carries_data_hashed_data_and_tokens(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
                hashed_data={"email": [{"data": "a1b2c3", "hashName": "hash1"}]},
                table_name="t1",
                http_code=200,
            ),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.get(GetRequest(table_name="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["table_name"], "t1")
        self.assertEqual(record["data"], {"name": "john doe"})
        self.assertEqual(record["hashed_data"], {"email": [{"data": "a1b2c3", "hash_name": "hash1"}]})
        self.assertEqual(record["tokens"], {"name": [{"token": "tok1", "token_group_name": "deterministic_string", "path": None}]})
        self.assertEqual(record["http_code"], 200)
        self.assertIsNone(record["error"])

    def test_success_and_error_records_in_one_list(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}, http_code=200),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.get(GetRequest(table_name="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0]["data"], {"a": 1})
        self.assertIsNone(response.records[0]["error"])
        self.assertEqual(response.records[1]["error"], "not found")
        self.assertEqual(response.records[1]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_id_as_an_error(self):
        self.get_api.with_raw_response.get_records.side_effect = Exception("network blip")

        response = self.vault.get(GetRequest(table_name="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertTrue(all("network blip" in r["error"] for r in response.records))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.get_api.with_raw_response.get_records.side_effect = api_error

        response = self.vault.get(GetRequest(table_name="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(response.records[0]["error"], "not found")
        self.assertEqual(response.records[0]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", ids=["id1"]))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


def fake_update_raw_response(records, headers=None):
    return SimpleNamespace(data=SimpleNamespace(records=records), headers=headers or {})


class TestVaultUpdate(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.update_api = MagicMock()
        self.vault_client.get_records_api.return_value = self.update_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_update_request")
    def test_update_validates_before_initializing_client(self, mock_validate):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1")

        self.vault.update(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_update_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(records=[], table_name="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_update_raises_on_empty_key(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(
                records=[{"skyflow_id": "id1", "data": {"": "value"}}], table_name="t1",
            ))
        self.update_api.with_raw_response.update_records.assert_not_called()

    def test_update_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(
                records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="   ",
            ))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1",
        )

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(len(kwargs["records"]), 1)
        self.assertEqual(kwargs["records"][0].skyflow_id, "id1")
        self.assertEqual(kwargs["records"][0].data, {"a": 1})
        self.assertIsNone(kwargs["records"][0].table_name)

    def test_maps_per_record_table_when_request_level_unset(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[
            {"skyflow_id": "id1", "data": {"a": 1}, "table_name": "t2"},
        ])

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertIsNone(kwargs["table_name"])
        self.assertEqual(kwargs["records"][0].table_name, "t2")

    def test_update_type_is_not_sent_to_the_update_endpoint(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1", update_type=UpsertType.REPLACE,
        )

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertNotIn("update_type", kwargs)

    # ------------------------------------------------------------------ #
    # response shape -- includes data, like get
    # ------------------------------------------------------------------ #

    def test_successful_records_include_data_and_tokens(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
            ),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"name": "john doe"}}], table_name="t1",
        ))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["name"], "tok1")
        self.assertEqual(record["data"], {"name": "john doe"})
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_records_are_split(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.update(UpdateRequest(records=[
            {"skyflow_id": "id1", "data": {"a": 1}},
            {"skyflow_id": "id2", "data": {"a": 2}},
        ], table_name="t1"))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_record_as_an_error(self):
        self.update_api.with_raw_response.update_records.side_effect = Exception("network blip")
        records = [{"skyflow_id": "id1", "data": {"a": 1}}, {"skyflow_id": "id2", "data": {"a": 2}}]

        response = self.vault.update(UpdateRequest(records=records, table_name="t1"))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.update_api.with_raw_response.update_records.side_effect = api_error

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1",
        ))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

    def test_success_record_with_hashed_data_and_scalar_tokens(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": "tok1"},
                hashed_data={"email": "hashed"},
            ),
        ], headers={"x-request-id": "req-h"})

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1",
        ))

        record = response.records[0]
        self.assertEqual(record["name"], "tok1")
        self.assertEqual(record["hashed_data"], {"email": "hashed"})

    def test_api_error_with_string_error_body_marks_every_record(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={"x-request-id": "req-s"}, body={"error": "server exploded"},
        )

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}, {"skyflow_id": "id2", "data": {"a": 2}}],
            table_name="t1",
        ))

        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all(e["error"] == "server exploded" for e in response.errors))
        self.assertTrue(all(e["code"] == 500 for e in response.errors))

    def test_api_error_with_dict_error_body_marks_every_record(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={"x-request-id": "req-d"},
            body={"error": {"message": "boom", "httpCode": 500}},
        )

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1",
        ))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "boom")

    def test_api_error_without_error_or_records_falls_back_to_exception_string(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={}, body={"foo": "bar"},
        )

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1",
        ))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["code"], 500)

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])

        self.vault.update(UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1"))

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


def fake_delete_raw_response(records, headers=None):
    return SimpleNamespace(data=SimpleNamespace(records=records), headers=headers or {})


class TestVaultDelete(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.delete_api = MagicMock()
        self.vault_client.get_records_api.return_value = self.delete_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_delete_request")
    def test_delete_validates_before_initializing_client(self, mock_validate):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([])
        request = DeleteRequest(table_name="t1", ids=["id1"])

        self.vault.delete(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_delete_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.delete(DeleteRequest(table_name="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_delete_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.delete(DeleteRequest(table_name="   ", ids=["id1"]))
        self.delete_api.with_raw_response.delete_records.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_table_and_ids(self):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table_name="t1", ids=["id1", "id2"]))

        _, kwargs = self.delete_api.with_raw_response.delete_records.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(kwargs["skyflow_i_ds"], ["id1", "id2"])

    def test_maps_unique_values(self):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table_name="t1", unique_values=[{"email": "a@b.com"}]))

        _, kwargs = self.delete_api.with_raw_response.delete_records.call_args
        self.assertEqual(len(kwargs["unique_values"]), 1)
        self.assertEqual(kwargs["unique_values"][0].data, {"email": "a@b.com"})

    # ------------------------------------------------------------------ #
    # response shape -- unified records list; delete rows carry only skyflow_id/http_code/error
    # ------------------------------------------------------------------ #

    def test_successful_record_carries_skyflow_id_and_http_code(self):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([
            FakeDeleteResponseObject(skyflow_id="id1", http_code=200),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["http_code"], 200)
        self.assertIsNone(record["error"])
        self.assertNotIn("data", record)
        self.assertNotIn("tokens", record)

    def test_success_and_error_records_in_one_list(self):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([
            FakeDeleteResponseObject(skyflow_id="id1", http_code=200),
            FakeDeleteResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0]["skyflow_id"], "id1")
        self.assertEqual(response.records[1]["error"], "not found")
        self.assertEqual(response.records[1]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_id_as_an_error(self):
        self.delete_api.with_raw_response.delete_records.side_effect = Exception("network blip")

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertTrue(all("network blip" in r["error"] for r in response.records))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.delete_api.with_raw_response.delete_records.side_effect = api_error

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(response.records[0]["error"], "not found")
        self.assertEqual(response.records[0]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table_name="t1", ids=["id1"]))

        _, kwargs = self.delete_api.with_raw_response.delete_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


def fake_detokenize_raw_response(response, headers=None):
    return SimpleNamespace(data=SimpleNamespace(response=response), headers=headers or {})


class TestVaultDetokenize(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.detokenize_api = MagicMock()
        self.vault_client.get_tokens_api.return_value = self.detokenize_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_detokenize_request")
    def test_detokenize_validates_before_initializing_client(self, mock_validate):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([])
        request = DetokenizeRequest(tokens=["tok1"])

        self.vault.detokenize(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_detokenize_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.detokenize(DetokenizeRequest(tokens=[]))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_tokens(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([])

        self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        _, kwargs = self.detokenize_api.with_raw_response.detokenize.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["tokens"], ["tok1", "tok2"])

    def test_maps_token_group_redactions(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([])

        self.vault.detokenize(DetokenizeRequest(
            tokens=["tok1"], token_group_redactions=[{"token_group_name": "g1", "redaction": "mask1"}],
        ))

        _, kwargs = self.detokenize_api.with_raw_response.detokenize.call_args
        self.assertEqual(len(kwargs["token_group_redactions"]), 1)
        self.assertEqual(kwargs["token_group_redactions"][0].token_group_name, "g1")
        self.assertEqual(kwargs["token_group_redactions"][0].redaction, "mask1")

    # ------------------------------------------------------------------ #
    # response shape -- unified records list; metadata normalized to snake_case
    # ------------------------------------------------------------------ #

    def test_successful_record_carries_value_group_and_metadata(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([
            FakeDetokenizeResponseObject(
                token="tok1", value="john doe", token_group_name="deterministic_string",
                http_code=200, metadata={"skyflowID": "sid", "tableName": "t1"},
            ),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["token"], "tok1")
        self.assertEqual(record["value"], "john doe")
        self.assertEqual(record["token_group_name"], "deterministic_string")
        self.assertEqual(record["metadata"], {"skyflow_id": "sid", "table_name": "t1"})
        self.assertEqual(record["http_code"], 200)
        self.assertIsNone(record["error"])

    def test_success_and_error_records_in_one_list(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([
            FakeDetokenizeResponseObject(token="tok1", value="john doe", http_code=200),
            FakeDetokenizeResponseObject(token="tok2", error="invalid token", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0]["value"], "john doe")
        self.assertEqual(response.records[1]["token"], "tok2")
        self.assertEqual(response.records[1]["error"], "invalid token")
        self.assertEqual(response.records[1]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_token_as_an_error(self):
        self.detokenize_api.with_raw_response.detokenize.side_effect = Exception("network blip")

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        self.assertEqual(len(response.records), 2)
        self.assertTrue(all("network blip" in r["error"] for r in response.records))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "invalid token", "httpCode": 404}]},
        )
        self.detokenize_api.with_raw_response.detokenize.side_effect = api_error

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(response.records[0]["error"], "invalid token")
        self.assertEqual(response.records[0]["http_code"], 404)

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([])

        self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))

        _, kwargs = self.detokenize_api.with_raw_response.detokenize.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


def fake_query_raw_response(records, headers=None, metadata=None):
    return SimpleNamespace(data=SimpleNamespace(records=records, metadata=metadata), headers=headers or {})


class TestVaultQuery(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.query_api = MagicMock()
        self.vault_client.get_query_api.return_value = self.query_api
        self.vault = VaultController(self.vault_client)

    @patch("skyflow_flowvault.vault.controller._vault.validate_query_request")
    def test_query_validates_before_initializing_client(self, mock_validate):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([])
        request = QueryRequest(query="SELECT * FROM t1")

        self.vault.query(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_query_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.query(QueryRequest(query="   "))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_maps_query(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([])

        self.vault.query(QueryRequest(query="SELECT * FROM t1 WHERE a = 1"))

        _, kwargs = self.query_api.with_raw_response.execute_query.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["query"], "SELECT * FROM t1 WHERE a = 1")

    def test_records_carry_data_and_metadata_columns(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response(
            [FakeExecuteQueryRecord(data={"a": 1}), FakeExecuteQueryRecord(data={"a": 2})],
            headers={"x-request-id": "req-1"},
            metadata=SimpleNamespace(columns=["a"]),
        )

        response = self.vault.query(QueryRequest(query="SELECT * FROM t1"))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0], {"data": {"a": 1}})
        self.assertEqual(response.records[1], {"data": {"a": 2}})
        self.assertEqual(response.metadata, {"columns": ["a"]})

    def test_transport_exception_produces_a_single_error_record(self):
        self.query_api.with_raw_response.execute_query.side_effect = Exception("network blip")

        response = self.vault.query(QueryRequest(query="SELECT * FROM t1"))

        self.assertEqual(len(response.records), 1)
        self.assertIn("network blip", response.records[0]["error"])
        self.assertIsNone(response.metadata)

    def test_api_error_with_flat_body_surfaces_the_error(self):
        api_error = ApiError(status_code=400, headers={"x-request-id": "req-3"}, body={"error": "bad query"})
        self.query_api.with_raw_response.execute_query.side_effect = api_error

        response = self.vault.query(QueryRequest(query="SELECT bad"))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(response.records[0]["error"], "bad query")
        self.assertEqual(response.records[0]["http_code"], 400)

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([])

        self.vault.query(QueryRequest(query="SELECT * FROM t1"))

        _, kwargs = self.query_api.with_raw_response.execute_query.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


def fake_bulk_insert_call(**kwargs):
    records = [
        FakeRecordResponseObject(skyflow_id=f"id-{i}", http_code=200)
        for i in range(len(kwargs["records"]))
    ]
    return FakeRawResponse(records, headers={"x-request-id": "req"})


def fake_bulk_detokenize_call(**kwargs):
    response = [
        FakeDetokenizeResponseObject(token=t, value=f"v-{t}", token_group_name="g", http_code=200)
        for t in kwargs["tokens"]
    ]
    return SimpleNamespace(data=SimpleNamespace(response=response), headers={"x-request-id": "req"})


class TestVaultBulkInsert(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.records_api = MagicMock()
        self.vault_client.get_records_api.return_value = self.records_api
        self.vault = VaultController(self.vault_client)
        env = patch.dict(os.environ, {"INSERT_BATCH_SIZE": "2", "INSERT_CONCURRENCY_LIMIT": "1"})
        env.start()
        self.addCleanup(env.stop)

    def _request(self, n):
        return BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(n)], table_name="t1")

    def test_splits_into_batches_and_merges_in_order(self):
        self.records_api.with_raw_response.insert_records.side_effect = fake_bulk_insert_call

        response = self.vault.bulk_insert(self._request(3))

        self.assertEqual(self.records_api.with_raw_response.insert_records.call_count, 2)
        self.assertEqual([r["index"] for r in response.records], [0, 1, 2])
        self.assertEqual(response.summary.total_records, 3)
        self.assertEqual(response.summary.total_inserted, 3)
        self.assertEqual(response.summary.total_failed, 0)

    def test_large_payload_indexing_is_contiguous_and_aligned_under_concurrency(self):
        # Each wire record's data['a'] IS its original input index, so the fake echoes it back
        # as skyflow_id -- letting us assert every merged record's index lines up with the exact
        # input it came from, even across 10 concurrent batches completing in any order.
        def side_effect(**kwargs):
            return FakeRawResponse(
                [FakeRecordResponseObject(skyflow_id=f"id-{rec.data['a']}", http_code=200) for rec in kwargs["records"]]
            )

        self.records_api.with_raw_response.insert_records.side_effect = side_effect
        request = BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(500)], table_name="t1")

        with patch.dict(os.environ, {"INSERT_BATCH_SIZE": "50", "INSERT_CONCURRENCY_LIMIT": "10"}):
            response = self.vault.bulk_insert(request)

        self.assertEqual(self.records_api.with_raw_response.insert_records.call_count, 10)  # 500 / 50
        self.assertEqual([r["index"] for r in response.records], list(range(500)))  # contiguous, in order, no gaps/dupes
        self.assertTrue(all(r["skyflow_id"] == f"id-{r['index']}" for r in response.records))  # index aligns with input
        self.assertEqual(response.summary.total_records, 500)
        self.assertEqual(response.summary.total_inserted, 500)
        self.assertEqual(response.summary.total_failed, 0)

    def test_large_payload_failing_middle_batch_keeps_correct_indices(self):
        # The batch covering indices 200..249 fails wholesale; every other batch succeeds.
        def side_effect(**kwargs):
            if kwargs["records"][0].data["a"] == 200:
                raise ApiError(status_code=500, headers={"x-request-id": "req-err"}, body={"error": "boom"})
            return FakeRawResponse(
                [FakeRecordResponseObject(skyflow_id=f"id-{rec.data['a']}", http_code=200) for rec in kwargs["records"]]
            )

        self.records_api.with_raw_response.insert_records.side_effect = side_effect
        request = BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(500)], table_name="t1")

        with patch.dict(os.environ, {"INSERT_BATCH_SIZE": "50", "INSERT_CONCURRENCY_LIMIT": "10"}):
            response = self.vault.bulk_insert(request)

        self.assertEqual([r["index"] for r in response.records], list(range(500)))
        failed = [r["index"] for r in response.records if r["error"] is not None]
        self.assertEqual(failed, list(range(200, 250)))  # exactly the failed batch's indices
        self.assertTrue(all(response.records[i]["http_code"] == 500 for i in range(200, 250)))
        self.assertEqual(response.summary.total_failed, 50)
        self.assertEqual(response.summary.total_inserted, 450)
        # 500 is retryable -> exactly the original records at those indices come back, in order
        retry = response.records_to_retry()
        self.assertEqual([r.data["a"] for r in retry], list(range(200, 250)))

    def test_tokens_and_hashed_data_are_normalized(self):
        self.records_api.with_raw_response.insert_records.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id0",
                tokens={"ssn": [{"token": "t1", "tokenGroupName": "g1", "path": "p"}]},
                hashed_data={"ssn": [{"data": "h", "hashName": "hash1"}]},
                http_code=200,
            ),
        ], headers={"x-request-id": "req"})

        response = self.vault.bulk_insert(self._request(1))

        record = response.records[0]
        self.assertEqual(record["tokens"], {"ssn": [{"token": "t1", "token_group_name": "g1", "path": "p"}]})
        self.assertEqual(record["hashed_data"], {"ssn": [{"data": "h", "hash_name": "hash1"}]})

    def test_failed_batch_marks_its_records_and_reports_summary(self):
        calls = {"n": 0}

        def side_effect(**kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise ApiError(status_code=500, headers={"x-request-id": "req-err"}, body={"error": "boom"})
            return fake_bulk_insert_call(**kwargs)

        self.records_api.with_raw_response.insert_records.side_effect = side_effect

        response = self.vault.bulk_insert(self._request(3))

        self.assertEqual(response.summary.total_records, 3)
        self.assertEqual(response.summary.total_inserted, 2)
        self.assertEqual(response.summary.total_failed, 1)
        failed = [r for r in response.records if r["error"] is not None]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["index"], 2)
        self.assertEqual(failed[0]["http_code"], 500)
        self.assertEqual(failed[0]["request_id"], "req-err")
        # 500 is retryable -> the original record at index 2 comes back
        retry = response.records_to_retry()
        self.assertEqual(len(retry), 1)
        self.assertEqual(retry[0].data, {"a": 2})

    def test_client_error_batch_is_not_retryable(self):
        def side_effect(**kwargs):
            raise ApiError(status_code=400, headers={}, body={"error": "bad"})

        self.records_api.with_raw_response.insert_records.side_effect = side_effect

        response = self.vault.bulk_insert(self._request(2))
        self.assertEqual(response.summary.total_failed, 2)
        self.assertEqual(response.records_to_retry(), [])

    def test_validation_error_raises_without_api_call(self):
        with self.assertRaises(SkyflowError):
            self.vault.bulk_insert(BulkInsertRequest(records=[], table_name="t1"))
        self.records_api.with_raw_response.insert_records.assert_not_called()

    def test_injects_authorization_header(self):
        self.vault_client.get_current_bearer_token.return_value = "the-token"
        self.records_api.with_raw_response.insert_records.side_effect = fake_bulk_insert_call

        self.vault.bulk_insert(self._request(1))

        _, kwargs = self.records_api.with_raw_response.insert_records.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-token")

    def test_interceptor_adds_custom_headers_per_batch(self):
        self.vault_client.get_config.return_value = {}
        self.records_api.with_raw_response.insert_records.side_effect = fake_bulk_insert_call
        seen = []

        def interceptor(context):
            seen.append((context.operation, context.batch_index, context.total_batches))
            context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, f"req-{context.batch_index}")

        self.vault.bulk_insert(self._request(3), BulkInsertOptions(interceptor=interceptor))

        self.assertEqual(seen, [("INSERT", 0, 2), ("INSERT", 1, 2)])
        calls = self.records_api.with_raw_response.insert_records.call_args_list
        self.assertEqual(calls[0].kwargs["request_options"]["additional_headers"]["x-request-id"], "req-0")
        self.assertEqual(calls[1].kwargs["request_options"]["additional_headers"]["x-request-id"], "req-1")

    def test_no_options_sends_no_custom_headers(self):
        self.records_api.with_raw_response.insert_records.side_effect = fake_bulk_insert_call

        self.vault.bulk_insert(self._request(1))

        _, kwargs = self.records_api.with_raw_response.insert_records.call_args
        self.assertNotIn("x-request-id", kwargs["request_options"]["additional_headers"])


class TestVaultBulkDetokenize(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.tokens_api = MagicMock()
        self.vault_client.get_tokens_api.return_value = self.tokens_api
        self.vault = VaultController(self.vault_client)
        env = patch.dict(os.environ, {"DETOKENIZE_BATCH_SIZE": "2", "DETOKENIZE_CONCURRENCY_LIMIT": "1"})
        env.start()
        self.addCleanup(env.stop)

    def test_splits_into_batches_and_merges_in_order(self):
        self.tokens_api.with_raw_response.detokenize.side_effect = fake_bulk_detokenize_call

        response = self.vault.bulk_detokenize(BulkDetokenizeRequest(tokens=["t0", "t1", "t2"]))

        self.assertEqual(self.tokens_api.with_raw_response.detokenize.call_count, 2)
        self.assertEqual([r["index"] for r in response.records], [0, 1, 2])
        self.assertEqual(response.records[0]["token"], "t0")
        self.assertEqual(response.records[0]["value"], "v-t0")
        self.assertEqual(response.summary.total_tokens, 3)
        self.assertEqual(response.summary.total_detokenized, 3)
        self.assertEqual(response.summary.total_failed, 0)

    def test_large_payload_indexing_is_contiguous_and_aligned_under_concurrency(self):
        self.tokens_api.with_raw_response.detokenize.side_effect = fake_bulk_detokenize_call
        tokens = [f"t{i}" for i in range(300)]

        with patch.dict(os.environ, {"DETOKENIZE_BATCH_SIZE": "50", "DETOKENIZE_CONCURRENCY_LIMIT": "10"}):
            response = self.vault.bulk_detokenize(BulkDetokenizeRequest(tokens=tokens))

        self.assertEqual(self.tokens_api.with_raw_response.detokenize.call_count, 6)  # 300 / 50
        self.assertEqual([r["index"] for r in response.records], list(range(300)))
        # each merged record's token/value line up with its original input position
        self.assertTrue(all(r["token"] == f"t{r['index']}" for r in response.records))
        self.assertTrue(all(r["value"] == f"v-t{r['index']}" for r in response.records))
        self.assertEqual(response.summary.total_tokens, 300)
        self.assertEqual(response.summary.total_detokenized, 300)

    def test_failed_batch_is_retryable_on_5xx(self):
        calls = {"n": 0}

        def side_effect(**kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise ApiError(status_code=503, headers={"x-request-id": "req-err"}, body={"error": "boom"})
            return fake_bulk_detokenize_call(**kwargs)

        self.tokens_api.with_raw_response.detokenize.side_effect = side_effect

        response = self.vault.bulk_detokenize(BulkDetokenizeRequest(tokens=["t0", "t1", "t2"]))

        self.assertEqual(response.summary.total_failed, 2)  # first batch (t0, t1) failed
        self.assertEqual(sorted(response.tokens_to_retry()), ["t0", "t1"])

    def test_validation_error_raises_without_api_call(self):
        with self.assertRaises(SkyflowError):
            self.vault.bulk_detokenize(BulkDetokenizeRequest(tokens=[]))
        self.tokens_api.with_raw_response.detokenize.assert_not_called()

    def test_interceptor_adds_custom_headers_per_batch(self):
        self.vault_client.get_config.return_value = {}
        self.tokens_api.with_raw_response.detokenize.side_effect = fake_bulk_detokenize_call
        seen = []

        def interceptor(context):
            seen.append((context.operation, context.batch_index, context.total_batches))
            context.add_header(CustomHeaderKey.SKYFLOW_ACCOUNT_ID, f"acct-{context.batch_index}")

        self.vault.bulk_detokenize(
            BulkDetokenizeRequest(tokens=["t0", "t1", "t2"]),
            BulkDetokenizeOptions(interceptor=interceptor),
        )

        self.assertEqual(seen, [("DETOKENIZE", 0, 2), ("DETOKENIZE", 1, 2)])
        calls = self.tokens_api.with_raw_response.detokenize.call_args_list
        self.assertEqual(calls[0].kwargs["request_options"]["additional_headers"]["x-skyflow-account-id"], "acct-0")
        self.assertEqual(calls[1].kwargs["request_options"]["additional_headers"]["x-skyflow-account-id"], "acct-1")


class TestVaultBulkInsertAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.records_api = MagicMock()
        self.records_api.with_raw_response.insert_records = AsyncMock(side_effect=fake_bulk_insert_call)
        self.vault_client.get_async_records_api.return_value = self.records_api
        self.vault = VaultController(self.vault_client)
        env = patch.dict(os.environ, {"INSERT_BATCH_SIZE": "2", "INSERT_CONCURRENCY_LIMIT": "2"})
        env.start()
        self.addCleanup(env.stop)

    async def test_bulk_insert_async_batches_and_merges(self):
        request = BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(3)], table_name="t1")

        response = await self.vault.bulk_insert_async(request)

        self.assertEqual(self.records_api.with_raw_response.insert_records.await_count, 2)
        self.assertEqual([r["index"] for r in response.records], [0, 1, 2])
        self.assertEqual(response.summary.total_records, 3)
        self.assertEqual(response.summary.total_inserted, 3)

    async def test_large_payload_indexing_survives_out_of_order_completion(self):
        # Earlier batches sleep longest, so batches COMPLETE in reverse order -- proves the merge
        # is by submission order (index), not completion order, across 10 concurrent batches.
        async def side_effect(**kwargs):
            first = kwargs["records"][0].data["a"]
            await asyncio.sleep((500 - first) / 100000.0)
            return FakeRawResponse(
                [FakeRecordResponseObject(skyflow_id=f"id-{rec.data['a']}", http_code=200) for rec in kwargs["records"]]
            )

        self.records_api.with_raw_response.insert_records = AsyncMock(side_effect=side_effect)
        self.vault_client.get_async_records_api.return_value = self.records_api
        request = BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(500)], table_name="t1")

        with patch.dict(os.environ, {"INSERT_BATCH_SIZE": "50", "INSERT_CONCURRENCY_LIMIT": "10"}):
            response = await self.vault.bulk_insert_async(request)

        self.assertEqual(self.records_api.with_raw_response.insert_records.await_count, 10)
        self.assertEqual([r["index"] for r in response.records], list(range(500)))
        self.assertTrue(all(r["skyflow_id"] == f"id-{r['index']}" for r in response.records))
        self.assertEqual(response.summary.total_inserted, 500)

    async def test_bulk_insert_async_batch_error_produces_error_rows(self):
        self.records_api.with_raw_response.insert_records = AsyncMock(
            side_effect=ApiError(status_code=500, headers={"x-request-id": "req-e"}, body={}))
        self.vault_client.get_async_records_api.return_value = self.records_api
        request = BulkInsertRequest(records=[BulkInsertRequestRecord(data={"a": i}) for i in range(3)], table_name="t1")

        response = await self.vault.bulk_insert_async(request)

        self.assertEqual(len(response.records), 3)
        self.assertTrue(all(r["error"] is not None for r in response.records))
        self.assertEqual(response.summary.total_inserted, 0)
        self.assertEqual(response.summary.total_failed, 3)


class TestVaultBulkDetokenizeAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.tokens_api = MagicMock()
        self.tokens_api.with_raw_response.detokenize = AsyncMock(side_effect=fake_bulk_detokenize_call)
        self.vault_client.get_async_tokens_api.return_value = self.tokens_api
        self.vault = VaultController(self.vault_client)
        env = patch.dict(os.environ, {"DETOKENIZE_BATCH_SIZE": "2", "DETOKENIZE_CONCURRENCY_LIMIT": "2"})
        env.start()
        self.addCleanup(env.stop)

    async def test_bulk_detokenize_async_batches_and_merges(self):
        response = await self.vault.bulk_detokenize_async(BulkDetokenizeRequest(tokens=["t0", "t1", "t2"]))

        self.assertEqual(self.tokens_api.with_raw_response.detokenize.await_count, 2)
        self.assertEqual([r["index"] for r in response.records], [0, 1, 2])
        self.assertEqual(response.summary.total_tokens, 3)
        self.assertEqual(response.summary.total_detokenized, 3)

    async def test_bulk_detokenize_async_batch_error_produces_error_rows(self):
        self.tokens_api.with_raw_response.detokenize = AsyncMock(
            side_effect=ApiError(status_code=500, headers={"x-request-id": "req-e"}, body={}))
        self.vault_client.get_async_tokens_api.return_value = self.tokens_api

        response = await self.vault.bulk_detokenize_async(BulkDetokenizeRequest(tokens=["t0", "t1", "t2"]))

        self.assertEqual(len(response.records), 3)
        self.assertTrue(all(r["error"] is not None for r in response.records))
        self.assertEqual(response.summary.total_failed, 3)


if __name__ == "__main__":
    unittest.main()
