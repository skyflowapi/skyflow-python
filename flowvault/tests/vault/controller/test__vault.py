import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow.generated.rest.core import ApiError
from skyflow.vault.controller import VaultController
from skyflow.vault.data import (
    UpsertOptions,
    ColumnRedactions,
    InsertRequestRecord,
    InsertRequest,
    GetRequest,
    GetRequestRecord,
    UpdateRequest,
    UpdateRequestRecord,
    DeleteRequest,
    DetokenizeRequest,
    InsertOptions,
    TokenGroupRedactions,
)
from skyflow.utils.enums import UpsertType, CustomHeaderKey


def tokens_as_dicts(tokens):
    if tokens is None:
        return None
    return {
        column: [
            {"token": t.token, "token_group_name": t.token_group_name, "path": t.path}
            for t in entries
        ]
        for column, entries in tokens.items()
    }


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

    def test_unary_interceptor_adds_custom_header(self):
        self.insert_api.with_raw_response.insert_records.return_value = FakeRawResponse([])
        seen = []

        def interceptor(context):
            seen.append((context.operation, context.batch_index, context.total_batches))
            context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, "req-x")

        self.vault.insert(
            InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"),
            InsertOptions(interceptor=interceptor),
        )

        _, kwargs = self.insert_api.with_raw_response.insert_records.call_args
        self.assertEqual(kwargs["request_options"]["additional_headers"]["x-request-id"], "req-x")
        self.assertEqual(seen, [("INSERT", -1, -1)])

    @patch("skyflow.vault.controller._vault.validate_insert_request")
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
        self.assertEqual(record.skyflow_id, "id1")
        self.assertEqual(record.table_name, "table1")
        self.assertEqual(tokens_as_dicts(record.tokens), {"name": [{"token": "tok1", "token_group_name": "deterministic_string", "path": "p"}]})
        self.assertEqual(record.data, {"name": "john doe"})
        self.assertEqual(record.hashed_data, {"name": [{"data": "h", "hash_name": "hash1"}]})
        self.assertEqual(record.http_code, 200)
        self.assertIsNone(record.error)

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

        self.assertEqual(tokens_as_dicts(response.records[0].tokens)["email"], [
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
        self.assertEqual(response.records[0].skyflow_id, "id1")
        self.assertIsNone(response.records[0].error)
        self.assertEqual(response.records[1].error, "bad row")
        self.assertEqual(response.records[1].http_code, 400)
        self.assertIsNone(response.records[1].skyflow_id)

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
        self.assertEqual([r.skyflow_id for r in response.records], ["id-0", "id-1", "id-2", "id-3"])

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_raises_skyflow_error(self):
        self.insert_api.with_raw_response.insert_records.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
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
        record = response.records[0]
        self.assertIn("notNull", record.error)
        self.assertEqual(record.http_code, 400)
        self.assertEqual(record.request_id, "req-3")

    def test_api_error_with_flat_body_raises_with_status_and_message(self):
        api_error = ApiError(status_code=500, headers={}, body={"error": "internal error"})
        self.insert_api.with_raw_response.insert_records.side_effect = api_error

        with self.assertRaises(SkyflowError) as ctx:
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"))
        self.assertEqual(ctx.exception.message, "internal error")
        self.assertEqual(ctx.exception.http_code, 500)

    def test_skyflow_error_from_api_call_propagates_unchanged(self):
        original = SkyflowError(message="already wrapped", http_code=418)
        self.insert_api.with_raw_response.insert_records.side_effect = original
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.insert(InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1"))
        self.assertIs(ctx.exception, original)

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

    @patch("skyflow.vault.controller._vault.validate_get_request")
    def test_get_validates_before_initializing_client(self, mock_validate):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])
        request = GetRequest(table_name="t1", skyflow_ids=["id1"])

        self.vault.get(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_get_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table_name="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_get_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table_name="   ", skyflow_ids=["id1"]))
        self.get_api.with_raw_response.get_records.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_table_and_ids(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1", "id2"]))

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
            GetRequestRecord(table_name="persons", skyflow_ids=["id1"], columns=["name"]),
            GetRequestRecord(table_name="cards", unique_values=[{"email": "a@b.com"}]),
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
            table_name="t1", skyflow_ids=["id1"], column_redactions=[ColumnRedactions(column_name="ssn", redaction="mask1")],
        ))

        _, kwargs = self.get_api.with_raw_response.get_records.call_args
        self.assertEqual(len(kwargs["column_redactions"]), 1)
        self.assertEqual(kwargs["column_redactions"][0].column_name, "ssn")
        self.assertEqual(kwargs["column_redactions"][0].redaction, "mask1")

    def test_maps_limit_offset_columns(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1"], columns=["a", "b"], limit=10, offset=5))

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

        response = self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.skyflow_id, "id1")
        self.assertEqual(record.table_name, "t1")
        self.assertEqual(record.data, {"name": "john doe"})
        self.assertEqual(record.hashed_data, {"email": [{"data": "a1b2c3", "hash_name": "hash1"}]})
        self.assertEqual(tokens_as_dicts(record.tokens), {"name": [{"token": "tok1", "token_group_name": "deterministic_string", "path": None}]})
        self.assertEqual(record.http_code, 200)
        self.assertIsNone(record.error)

    def test_success_and_error_records_in_one_list(self):
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}, http_code=200),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0].data, {"a": 1})
        self.assertIsNone(response.records[0].error)
        self.assertEqual(response.records[1].error, "not found")
        self.assertEqual(response.records[1].http_code, 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_raises_skyflow_error(self):
        self.get_api.with_raw_response.get_records.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1", "id2"]))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.get_api.with_raw_response.get_records.side_effect = api_error

        response = self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1"]))
        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.error, "not found")
        self.assertEqual(record.http_code, 404)
        self.assertEqual(record.request_id, "req-3")

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.get_api.with_raw_response.get_records.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table_name="t1", skyflow_ids=["id1"]))

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

    @patch("skyflow.vault.controller._vault.validate_update_request")
    def test_update_validates_before_initializing_client(self, mock_validate):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1")

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
                records=[UpdateRequestRecord(skyflow_id='id1', data={'': 'value'})], table_name="t1",
            ))
        self.update_api.with_raw_response.update_records.assert_not_called()

    def test_update_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(
                records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="   ",
            ))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1",
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
            UpdateRequestRecord(skyflow_id='id1', data={'a': 1}, table_name='t2'),
        ])

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertIsNone(kwargs["table_name"])
        self.assertEqual(kwargs["records"][0].table_name, "t2")

    def test_update_type_is_sent_to_the_update_endpoint(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1", update_type=UpsertType.REPLACE,
        )

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertEqual(kwargs["update_type"], "REPLACE")

    def test_update_type_omitted_when_not_set(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertNotIn("update_type", kwargs)

    def test_byot_tokens_are_sent_on_update_record(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1}, tokens={'a': 'tok-a'})], table_name="t1",
        )

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update_records.call_args
        self.assertEqual(kwargs["records"][0].tokens, {"a": "tok-a"})

    def test_update_record_without_data_raises_skyflow_error(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1')], table_name="t1"))
        self.update_api.with_raw_response.update_records.assert_not_called()

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
            records=[UpdateRequestRecord(skyflow_id='id1', data={'name': 'john doe'})], table_name="t1",
        ))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.skyflow_id, "id1")
        self.assertEqual(tokens_as_dicts(record.tokens), {"name": [{"token": "tok1", "token_group_name": "deterministic_string", "path": None}]})
        self.assertEqual(record.data, {"name": "john doe"})
        self.assertIsNone(record.error)

    def test_mixed_success_and_error_records_are_split(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.update(UpdateRequest(records=[
            UpdateRequestRecord(skyflow_id='id1', data={'a': 1}),
            UpdateRequestRecord(skyflow_id='id2', data={'a': 2}),
        ], table_name="t1"))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0].skyflow_id, "id1")
        self.assertIsNone(response.records[0].error)
        self.assertEqual(response.records[1].error, "not found")
        self.assertEqual(response.records[1].http_code, 404)
        self.assertEqual(response.records[1].request_id, "req-2")

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_raises_skyflow_error(self):
        self.update_api.with_raw_response.update_records.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.update_api.with_raw_response.update_records.side_effect = api_error

        response = self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))
        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.error, "not found")
        self.assertEqual(record.http_code, 404)
        self.assertEqual(record.request_id, "req-3")

    def test_success_record_with_hashed_data_and_scalar_tokens(self):
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": "tok1"},
                hashed_data={"email": "hashed"},
            ),
        ], headers={"x-request-id": "req-h"})

        response = self.vault.update(UpdateRequest(
            records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1",
        ))

        record = response.records[0]
        self.assertEqual(tokens_as_dicts(record.tokens), {"name": [{"token": "tok1", "token_group_name": None, "path": None}]})
        self.assertEqual(record.hashed_data, {"email": [{"data": "hashed", "hash_name": None}]})

    def test_api_error_with_string_error_body_raises(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={"x-request-id": "req-s"}, body={"error": "server exploded"},
        )

        with self.assertRaises(SkyflowError) as ctx:
            self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))
        self.assertEqual(ctx.exception.message, "server exploded")
        self.assertEqual(ctx.exception.http_code, 500)

    def test_api_error_with_dict_error_body_raises(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={"x-request-id": "req-d"},
            body={"error": {"message": "boom", "httpCode": 500}},
        )

        with self.assertRaises(SkyflowError) as ctx:
            self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))
        self.assertEqual(ctx.exception.message, "boom")

    def test_api_error_without_error_or_records_raises_unknown(self):
        self.update_api.with_raw_response.update_records.side_effect = ApiError(
            status_code=500, headers={}, body={"foo": "bar"},
        )

        with self.assertRaises(SkyflowError) as ctx:
            self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))
        self.assertEqual(ctx.exception.http_code, 500)

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.update_api.with_raw_response.update_records.return_value = fake_update_raw_response([])

        self.vault.update(UpdateRequest(records=[UpdateRequestRecord(skyflow_id='id1', data={'a': 1})], table_name="t1"))

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

    @patch("skyflow.vault.controller._vault.validate_delete_request")
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
        self.assertEqual(record.skyflow_id, "id1")
        self.assertEqual(record.http_code, 200)
        self.assertIsNone(record.error)
        self.assertFalse(hasattr(record, "data"))
        self.assertFalse(hasattr(record, "tokens"))

    def test_success_and_error_records_in_one_list(self):
        self.delete_api.with_raw_response.delete_records.return_value = fake_delete_raw_response([
            FakeDeleteResponseObject(skyflow_id="id1", http_code=200),
            FakeDeleteResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0].skyflow_id, "id1")
        self.assertEqual(response.records[1].error, "not found")
        self.assertEqual(response.records[1].http_code, 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_raises_skyflow_error(self):
        self.delete_api.with_raw_response.delete_records.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.delete(DeleteRequest(table_name="t1", ids=["id1", "id2"]))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.delete_api.with_raw_response.delete_records.side_effect = api_error

        response = self.vault.delete(DeleteRequest(table_name="t1", ids=["id1"]))
        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.error, "not found")
        self.assertEqual(record.http_code, 404)
        self.assertEqual(record.request_id, "req-3")

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

    @patch("skyflow.vault.controller._vault.validate_detokenize_request")
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
            tokens=["tok1"], token_group_redactions=[TokenGroupRedactions(token_group_name="g1", redaction="mask1")],
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
        self.assertEqual(record.token, "tok1")
        self.assertEqual(record.value, "john doe")
        self.assertEqual(record.token_group_name, "deterministic_string")
        self.assertEqual(record.metadata.skyflow_id, "sid")
        self.assertEqual(record.metadata.table_name, "t1")
        self.assertEqual(record.http_code, 200)
        self.assertIsNone(record.error)

    def test_success_and_error_records_in_one_list(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([
            FakeDetokenizeResponseObject(token="tok1", value="john doe", http_code=200),
            FakeDetokenizeResponseObject(token="tok2", error="invalid token", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0].value, "john doe")
        self.assertEqual(response.records[1].token, "tok2")
        self.assertEqual(response.records[1].error, "invalid token")
        self.assertEqual(response.records[1].http_code, 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_raises_skyflow_error(self):
        self.detokenize_api.with_raw_response.detokenize.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "invalid token", "httpCode": 404}]},
        )
        self.detokenize_api.with_raw_response.detokenize.side_effect = api_error

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))
        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record.error, "invalid token")
        self.assertEqual(record.http_code, 404)
        self.assertEqual(record.request_id, "req-3")

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
