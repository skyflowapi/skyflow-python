import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.vault.controller import VaultController
from skyflow_flowvault.vault.data import (
    InsertRequest,
    GetRequest,
    UpdateRequest,
    DeleteRequest,
    DetokenizeRequest,
    TokenizeRequest,
)
from skyflow_flowvault.utils.enums import UpsertType


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


class FakeTokenizeResponseObjectToken:
    def __init__(self, token_group_name=None, token=None, error=None, http_code=None):
        self.token_group_name = token_group_name
        self.token = token
        self.error = error
        self.http_code = http_code


class FakeTokenizeResponseObject:
    def __init__(self, value=None, tokens=None):
        self.value = value
        self.tokens = tokens


class FakeV1InsertResponse:
    def __init__(self, records):
        self.records = records


class FakeRawResponse:
    """Stands in for the HttpResponse wrapper returned by with_raw_response.insert(...) --
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
        self.vault_client.get_flowservice_api.return_value = self.insert_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_insert_request")
    def test_insert_validates_before_initializing_client(self, mock_validate):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(values=[dict(values={"a": 1})], table="t1")

        self.vault.insert(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_insert_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[], table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # shared BaseVaultController validation helpers, exercised end-to-end via insert()
    # (unit-tested in isolation in common/tests/vault/test_base_vault_controller.py)
    # ------------------------------------------------------------------ #

    def test_insert_raises_on_empty_key(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[dict(values={"": "value"})], table="t1"))
        self.insert_api.with_raw_response.insert.assert_not_called()

    def test_insert_allows_empty_value(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        self.vault.insert(InsertRequest(values=[dict(values={"a": ""})], table="t1"))
        self.insert_api.with_raw_response.insert.assert_called_once()

    def test_insert_raises_on_non_dict_values(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[dict(values=["not", "a", "dict"])], table="t1"))

    def test_insert_raises_on_empty_values_dict(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[dict(values={})], table="t1"))

    def test_insert_raises_on_invalid_request_level_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[dict(values={"a": 1})], table="   "))

    def test_insert_raises_on_invalid_per_record_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(values=[dict(values={"a": 1}, table="   ")]))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table_and_upsert(self):
        """When no record sets its own table/upsert, both go ONLY at the request level -- the
        vault rejects sending table_name/upsert in both places (see the validation tests), so
        the wire records must NOT also carry a resolved copy."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(
            values=[dict(values={"a": 1})],
            table="t1",
            upsert={"update_type": UpsertType.REPLACE, "unique_columns": ["a"]},
        )

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
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
            values=[dict(values={"a": 1}, table="t2")],
            table="t1",
        )

        with self.assertRaises(SkyflowError):
            self.vault.insert(request)
        self.insert_api.with_raw_response.insert.assert_not_called()

    def test_per_record_table_and_upsert_used_when_request_level_unset(self):
        """Legitimate per-record use: no request-level table/upsert at all -- Java parity
        requires EVERY record to set its own table in this mode (see validation tests), so both
        records do; only the second also sets its own upsert."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(values=[
            dict(values={"a": 1}, table="t2", upsert={"unique_columns": ["b"]}),
            dict(values={"a": 2}, table="t2"),
        ])

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("table_name", kwargs)
        self.assertNotIn("upsert", kwargs)
        self.assertEqual(kwargs["records"][0].table_name, "t2")
        self.assertEqual(kwargs["records"][0].upsert.unique_columns, ["b"])
        self.assertEqual(kwargs["records"][1].table_name, "t2")
        self.assertIsNone(kwargs["records"][1].upsert)

    def test_no_request_level_table_is_omitted_not_sent_as_none(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(values=[dict(values={"a": 1}, table="t2")])  # no request-level table

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("table_name", kwargs)

    def test_wire_shape_matches_confirmed_working_request(self):
        """Regression pin for a real bug: a request with only per-record table/upsert (no
        request-level table/upsert at all) previously sent explicit `"tableName": null` /
        `"upsert": null` at the top level, which diverged from a hand-verified working request
        against a real vault (confirmed to have neither key present when unset)."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(values=[
            dict(
                values={"name": "saileshwar", "email": "nanana@gmail.com"},
                table="table1",
                upsert={"update_type": UpsertType.UPDATE, "unique_columns": ["email"]},
            ),
        ])

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("table_name", kwargs)
        self.assertNotIn("upsert", kwargs)
        self.assertEqual(kwargs["records"][0].table_name, "table1")
        self.assertEqual(kwargs["records"][0].upsert.update_type, "UPDATE")
        self.assertEqual(kwargs["records"][0].upsert.unique_columns, ["email"])

    def test_no_upsert_is_omitted_not_sent_as_none(self):
        """upsert must be OMITTED from the wire call entirely when unset, not passed as None --
        a real vault confirmed a working request never includes a null upsert/tableName key."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(values=[dict(values={"a": 1})], table="t1")

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("upsert", kwargs)
        self.assertIsNone(kwargs["records"][0].upsert)

    # ------------------------------------------------------------------ #
    # response shape -- mirrors PDB's InsertResponse (inserted_fields/errors)
    # ------------------------------------------------------------------ #

    def test_successful_records_go_to_inserted_fields(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
                table_name="table1",
            ),
        ], headers={"x-request-id": "req-1"})
        response = self.vault.insert(InsertRequest(values=[dict(values={"name": "john doe"})], table="table1"))

        self.assertEqual(len(response.inserted_fields), 1)
        inserted = response.inserted_fields[0]
        self.assertEqual(inserted["request_index"], 0)
        self.assertEqual(inserted["skyflow_id"], "id1")
        self.assertEqual(inserted["name"], "tok1")
        self.assertNotIn("data", inserted)
        self.assertNotIn("table", inserted)
        self.assertNotIn("tokens", inserted)
        self.assertIsNone(response.errors)

    def test_multiple_token_groups_for_one_field_flatten_to_a_list(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"email": [
                    {"token": "tok-det", "tokenGroupName": "deterministic_string"},
                    {"token": "tok-nondet", "tokenGroupName": "nondeterministic_string"},
                ]},
            ),
        ])
        response = self.vault.insert(InsertRequest(values=[dict(values={"email": "a@b.com"})], table="t1"))

        self.assertEqual(response.inserted_fields[0]["email"], ["tok-det", "tok-nondet"])

    def test_mixed_success_and_error_records_are_split(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(skyflow_id="id1", tokens=None),
            FakeRecordResponseObject(error="bad row", http_code=400, table_name="t1"),
        ], headers={"x-request-id": "req-2"})
        response = self.vault.insert(InsertRequest(
            values=[dict(values={"a": 1}), dict(values={"a": 2})], table="t1",
        ))

        self.assertEqual(len(response.inserted_fields), 1)
        self.assertEqual(response.inserted_fields[0]["request_index"], 0)
        self.assertEqual(response.inserted_fields[0]["skyflow_id"], "id1")
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["request_index"], 1)
        self.assertEqual(response.errors[0]["error"], "bad row")
        self.assertEqual(response.errors[0]["code"], 400)
        self.assertEqual(response.errors[0]["request_id"], "req-2")

    def test_error_record_identified_by_error_field_alone(self):
        """Mirrors Java's Utils.formatResponse exactly: a record is an error purely by .error
        being present -- http_code is read onto the error dict's 'code' key but is not itself
        part of the success/error decision."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(skyflow_id="id1", http_code=200),
        ])
        response = self.vault.insert(InsertRequest(values=[dict(values={"a": 1})], table="t1"))

        self.assertEqual(len(response.inserted_fields), 1)
        self.assertIsNone(response.errors)

    # ------------------------------------------------------------------ #
    # no batching -- every insert is exactly one API call
    # ------------------------------------------------------------------ #

    def test_all_records_sent_in_a_single_api_call_regardless_of_count(self):
        self.insert_api.with_raw_response.insert.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [dict(values={"a": i}) for i in range(4)]

        response = self.vault.insert(InsertRequest(values=records, table="t1"))

        self.insert_api.with_raw_response.insert.assert_called_once()
        call_size = len(self.insert_api.with_raw_response.insert.call_args.kwargs["records"])
        self.assertEqual(call_size, 4)
        self.assertEqual(len(response.inserted_fields), 4)

    def test_request_index_matches_position_in_the_original_records_list(self):
        self.insert_api.with_raw_response.insert.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [dict(values={"a": i}) for i in range(4)]

        response = self.vault.insert(InsertRequest(values=records, table="t1"))

        self.assertEqual(sorted(s["request_index"] for s in response.inserted_fields), [0, 1, 2, 3])

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_record_as_an_error(self):
        """Without batching, one API call carries every record -- a transport-level exception
        on that single call means every record in the request fails, not just some."""
        self.insert_api.with_raw_response.insert.side_effect = Exception("network blip")
        records = [dict(values={"a": 1}), dict(values={"a": 2})]

        response = self.vault.insert(InsertRequest(values=records, table="t1"))

        self.insert_api.with_raw_response.insert.assert_called_once()
        self.assertEqual(len(response.inserted_fields), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))
        self.assertEqual([e["request_index"] for e in response.errors], [0, 1])

    def test_api_error_with_structured_per_record_body_splits_into_one_error_per_row(self):
        """Mirrors Java's Utils.handleBatchException: a structured error body (a 'records' list)
        is split into individual error dicts instead of repeating one flat message for the
        whole batch -- shaped after a real vault's actual 400 response for a partial-batch
        failure (e.g. a NOT NULL column violation on one row)."""
        api_error = ApiError(
            status_code=400,
            headers={"x-request-id": "req-3"},
            body={"records": [
                {"error": "Column passport has the notNull attribute, and input contains a null value.",
                 "httpCode": 400},
            ]},
        )
        self.insert_api.with_raw_response.insert.side_effect = api_error

        response = self.vault.insert(InsertRequest(values=[dict(values={"name": "a"})], table="t1"))

        self.assertEqual(len(response.errors), 1)
        self.assertIn("notNull", response.errors[0]["error"])
        self.assertEqual(response.errors[0]["code"], 400)
        self.assertEqual(response.errors[0]["request_id"], "req-3")
        self.assertEqual(response.errors[0]["request_index"], 0)

    def test_api_error_with_flat_body_falls_back_to_one_error_per_record(self):
        api_error = ApiError(status_code=500, headers={}, body={"error": "internal error"})
        self.insert_api.with_raw_response.insert.side_effect = api_error

        response = self.vault.insert(InsertRequest(
            values=[dict(values={"a": 1}), dict(values={"a": 2})], table="t1",
        ))

        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all(e["error"] == "internal error" for e in response.errors))
        self.assertTrue(all(e["code"] == 500 for e in response.errors))
        self.assertEqual([e["request_index"] for e in response.errors], [0, 1])

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(values=[dict(values={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")

    def test_no_authorization_header_when_no_token_available(self):
        self.vault_client.get_current_bearer_token.return_value = None
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(values=[dict(values={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
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
        self.vault_client.get_flowservice_api.return_value = self.get_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_get_request")
    def test_get_validates_before_initializing_client(self, mock_validate):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])
        request = GetRequest(table="t1", ids=["id1"])

        self.vault.get(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_get_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_get_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.get(GetRequest(table="   ", ids=["id1"]))
        self.get_api.with_raw_response.get.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_table_and_ids(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table="t1", ids=["id1", "id2"]))

        _, kwargs = self.get_api.with_raw_response.get.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(kwargs["skyflow_i_ds"], ["id1", "id2"])

    def test_maps_unique_values(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table="t1", unique_values=[{"email": "a@b.com"}]))

        _, kwargs = self.get_api.with_raw_response.get.call_args
        self.assertEqual(len(kwargs["unique_values"]), 1)
        self.assertEqual(kwargs["unique_values"][0].data, {"email": "a@b.com"})

    def test_maps_column_redactions(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(
            table="t1", ids=["id1"], column_redactions=[{"column_name": "ssn", "redaction": "mask1"}],
        ))

        _, kwargs = self.get_api.with_raw_response.get.call_args
        self.assertEqual(len(kwargs["column_redactions"]), 1)
        self.assertEqual(kwargs["column_redactions"][0].column_name, "ssn")
        self.assertEqual(kwargs["column_redactions"][0].redaction, "mask1")

    def test_maps_limit_offset_columns(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table="t1", ids=["id1"], columns=["a", "b"], limit=10, offset=5))

        _, kwargs = self.get_api.with_raw_response.get.call_args
        self.assertEqual(kwargs["columns"], ["a", "b"])
        self.assertEqual(kwargs["limit"], 10)
        self.assertEqual(kwargs["offset"], 5)

    # ------------------------------------------------------------------ #
    # response shape -- includes data, unlike insert
    # ------------------------------------------------------------------ #

    def test_successful_records_include_data_and_tokens(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
                hashed_data={"name": "a1b2c3"},
                table_name="t1",
            ),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.get(GetRequest(table="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["hashed_data"], {"name": "a1b2c3"})
        self.assertEqual(record["request_index"], 0)
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["name"], "tok1")
        self.assertEqual(record["data"], {"name": "john doe"})
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_records_are_split(self):
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.get(GetRequest(table="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(response.records[0]["data"], {"a": 1})
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-2")

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_id_as_an_error(self):
        self.get_api.with_raw_response.get.side_effect = Exception("network blip")

        response = self.vault.get(GetRequest(table="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.get_api.with_raw_response.get.side_effect = api_error

        response = self.vault.get(GetRequest(table="t1", ids=["id1"]))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.get_api.with_raw_response.get.return_value = fake_get_raw_response([])

        self.vault.get(GetRequest(table="t1", ids=["id1"]))

        _, kwargs = self.get_api.with_raw_response.get.call_args
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
        self.vault_client.get_flowservice_api.return_value = self.update_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_update_request")
    def test_update_validates_before_initializing_client(self, mock_validate):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="t1")

        self.vault.update(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_update_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(records=[], table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_update_raises_on_empty_key(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(
                records=[{"skyflow_id": "id1", "values": {"": "value"}}], table="t1",
            ))
        self.update_api.with_raw_response.update.assert_not_called()

    def test_update_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.update(UpdateRequest(
                records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="   ",
            ))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table_and_update_type(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="t1", update_type=UpsertType.REPLACE,
        )

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(kwargs["update_type"], "REPLACE")
        self.assertEqual(len(kwargs["records"]), 1)
        self.assertEqual(kwargs["records"][0].skyflow_id, "id1")
        self.assertEqual(kwargs["records"][0].data, {"a": 1})
        self.assertIsNone(kwargs["records"][0].table_name)

    def test_maps_per_record_table_when_request_level_unset(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[
            {"skyflow_id": "id1", "values": {"a": 1}, "table": "t2"},
        ])

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update.call_args
        self.assertNotIn("table_name", kwargs)
        self.assertEqual(kwargs["records"][0].table_name, "t2")

    def test_maps_per_record_tokens(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[
            {"skyflow_id": "id1", "values": {"a": 1}, "tokens": {"a": "tok1"}, "table": "t1"},
        ])

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update.call_args
        self.assertEqual(kwargs["records"][0].tokens, {"a": "tok1"})

    def test_no_update_type_is_omitted_not_sent_as_none(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])
        request = UpdateRequest(records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="t1")

        self.vault.update(request)

        _, kwargs = self.update_api.with_raw_response.update.call_args
        self.assertNotIn("update_type", kwargs)

    # ------------------------------------------------------------------ #
    # response shape -- includes data, like get
    # ------------------------------------------------------------------ #

    def test_successful_records_include_data_and_tokens(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
            ),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "values": {"name": "john doe"}}], table="t1",
        ))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertEqual(record["name"], "tok1")
        self.assertEqual(record["data"], {"name": "john doe"})
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_records_are_split(self):
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([
            FakeRecordResponseObject(skyflow_id="id1", data={"a": 1}),
            FakeRecordResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.update(UpdateRequest(records=[
            {"skyflow_id": "id1", "values": {"a": 1}},
            {"skyflow_id": "id2", "values": {"a": 2}},
        ], table="t1"))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_record_as_an_error(self):
        self.update_api.with_raw_response.update.side_effect = Exception("network blip")
        records = [{"skyflow_id": "id1", "values": {"a": 1}}, {"skyflow_id": "id2", "values": {"a": 2}}]

        response = self.vault.update(UpdateRequest(records=records, table="t1"))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.update_api.with_raw_response.update.side_effect = api_error

        response = self.vault.update(UpdateRequest(
            records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="t1",
        ))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.update_api.with_raw_response.update.return_value = fake_update_raw_response([])

        self.vault.update(UpdateRequest(records=[{"skyflow_id": "id1", "values": {"a": 1}}], table="t1"))

        _, kwargs = self.update_api.with_raw_response.update.call_args
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
        self.vault_client.get_flowservice_api.return_value = self.delete_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_delete_request")
    def test_delete_validates_before_initializing_client(self, mock_validate):
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([])
        request = DeleteRequest(table="t1", ids=["id1"])

        self.vault.delete(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_delete_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.delete(DeleteRequest(table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_delete_raises_on_invalid_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.delete(DeleteRequest(table="   ", ids=["id1"]))
        self.delete_api.with_raw_response.delete.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_table_and_ids(self):
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table="t1", ids=["id1", "id2"]))

        _, kwargs = self.delete_api.with_raw_response.delete.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["table_name"], "t1")
        self.assertEqual(kwargs["skyflow_i_ds"], ["id1", "id2"])

    def test_maps_unique_values(self):
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table="t1", unique_values=[{"email": "a@b.com"}]))

        _, kwargs = self.delete_api.with_raw_response.delete.call_args
        self.assertEqual(len(kwargs["unique_values"]), 1)
        self.assertEqual(kwargs["unique_values"][0].data, {"email": "a@b.com"})

    # ------------------------------------------------------------------ #
    # response shape -- no tokens/data field at all on V1DeleteResponseObject;
    # this is the regression test pinning the getattr(..., 'tokens', None) fix
    # ------------------------------------------------------------------ #

    def test_successful_records_have_no_data_or_tokens_keys(self):
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([
            FakeDeleteResponseObject(skyflow_id="id1"),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.delete(DeleteRequest(table="t1", ids=["id1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["request_index"], 0)
        self.assertEqual(record["skyflow_id"], "id1")
        self.assertNotIn("data", record)
        self.assertNotIn("hashed_data", record)
        self.assertNotIn("tokens", record)
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_records_are_split(self):
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([
            FakeDeleteResponseObject(skyflow_id="id1"),
            FakeDeleteResponseObject(error="not found", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.delete(DeleteRequest(table="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_id_as_an_error(self):
        self.delete_api.with_raw_response.delete.side_effect = Exception("network blip")

        response = self.vault.delete(DeleteRequest(table="t1", ids=["id1", "id2"]))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "not found", "httpCode": 404}]},
        )
        self.delete_api.with_raw_response.delete.side_effect = api_error

        response = self.vault.delete(DeleteRequest(table="t1", ids=["id1"]))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.delete_api.with_raw_response.delete.return_value = fake_delete_raw_response([])

        self.vault.delete(DeleteRequest(table="t1", ids=["id1"]))

        _, kwargs = self.delete_api.with_raw_response.delete.call_args
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
        self.vault_client.get_flowservice_api.return_value = self.detokenize_api
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
    # response shape -- keyed by token, not skyflow_id
    # ------------------------------------------------------------------ #

    def test_successful_records_include_value_and_token_group_name(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([
            FakeDetokenizeResponseObject(token="tok1", value="john doe", token_group_name="deterministic_string"),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))

        self.assertEqual(len(response.records), 1)
        record = response.records[0]
        self.assertEqual(record["request_index"], 0)
        self.assertEqual(record["token"], "tok1")
        self.assertEqual(record["value"], "john doe")
        self.assertEqual(record["token_group_name"], "deterministic_string")
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_records_are_split(self):
        self.detokenize_api.with_raw_response.detokenize.return_value = fake_detokenize_raw_response([
            FakeDetokenizeResponseObject(token="tok1", value="john doe"),
            FakeDetokenizeResponseObject(token="tok2", error="invalid token", http_code=404),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["token"], "tok2")
        self.assertEqual(response.errors[0]["error"], "invalid token")
        self.assertEqual(response.errors[0]["code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_token_as_an_error(self):
        self.detokenize_api.with_raw_response.detokenize.side_effect = Exception("network blip")

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1", "tok2"]))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "invalid token", "httpCode": 404}]},
        )
        self.detokenize_api.with_raw_response.detokenize.side_effect = api_error

        response = self.vault.detokenize(DetokenizeRequest(tokens=["tok1"]))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "invalid token")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

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


def fake_tokenize_raw_response(response, headers=None):
    return SimpleNamespace(data=SimpleNamespace(response=response), headers=headers or {})


class TestVaultTokenize(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.tokenize_api = MagicMock()
        self.vault_client.get_flowservice_api.return_value = self.tokenize_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_tokenize_request")
    def test_tokenize_validates_before_initializing_client(self, mock_validate):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([])
        request = TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1"]}])

        self.vault.tokenize(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_tokenize_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.tokenize(TokenizeRequest(values=[]))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_values_and_token_group_names(self):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([])

        self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1", "g2"]}]))

        _, kwargs = self.tokenize_api.with_raw_response.tokenize.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(len(kwargs["data"]), 1)
        self.assertEqual(kwargs["data"][0].value, "a@b.com")
        self.assertEqual(kwargs["data"][0].token_group_names, ["g1", "g2"])

    def test_no_byot_token_is_omitted_not_sent_as_none(self):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([])

        self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1"]}]))

        _, kwargs = self.tokenize_api.with_raw_response.tokenize.call_args
        self.assertIsNone(kwargs["data"][0].token)

    def test_maps_byot_token_when_present(self):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([])

        self.vault.tokenize(TokenizeRequest(
            values=[{"value": "a@b.com", "token_group_names": ["g1"], "token": "custom-tok"}],
        ))

        _, kwargs = self.tokenize_api.with_raw_response.tokenize.call_args
        self.assertEqual(kwargs["data"][0].token, "custom-tok")

    # ------------------------------------------------------------------ #
    # response shape -- one value fans out to a list of per-token-group results
    # ------------------------------------------------------------------ #

    def test_successful_value_fans_out_to_one_record_per_token_group(self):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([
            FakeTokenizeResponseObject(value="a@b.com", tokens=[
                FakeTokenizeResponseObjectToken(token_group_name="g1", token="tok-g1"),
                FakeTokenizeResponseObjectToken(token_group_name="g2", token="tok-g2"),
            ]),
        ], headers={"x-request-id": "req-1"})

        response = self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1", "g2"]}]))

        self.assertEqual(len(response.records), 2)
        self.assertEqual(response.records[0]["value"], "a@b.com")
        self.assertEqual(response.records[0]["token_group_name"], "g1")
        self.assertEqual(response.records[0]["token"], "tok-g1")
        self.assertEqual(response.records[1]["token_group_name"], "g2")
        self.assertEqual(response.records[1]["token"], "tok-g2")
        self.assertIsNone(response.errors)

    def test_mixed_success_and_error_token_groups_are_split(self):
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([
            FakeTokenizeResponseObject(value="a@b.com", tokens=[
                FakeTokenizeResponseObjectToken(token_group_name="g1", token="tok-g1"),
                FakeTokenizeResponseObjectToken(token_group_name="g2", error="group not found", http_code=404),
            ]),
        ], headers={"x-request-id": "req-2"})

        response = self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1", "g2"]}]))

        self.assertEqual(len(response.records), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["token_group_name"], "g2")
        self.assertEqual(response.errors[0]["error"], "group not found")
        self.assertEqual(response.errors[0]["code"], 404)

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_value_as_an_error(self):
        self.tokenize_api.with_raw_response.tokenize.side_effect = Exception("network blip")
        values = [
            {"value": "a@b.com", "token_group_names": ["g1"]},
            {"value": "b@c.com", "token_group_names": ["g1"]},
        ]

        response = self.vault.tokenize(TokenizeRequest(values=values))

        self.assertEqual(len(response.records), 0)
        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all("network blip" in e["error"] for e in response.errors))

    def test_api_error_with_structured_body_splits_into_one_error_per_row(self):
        api_error = ApiError(
            status_code=404,
            headers={"x-request-id": "req-3"},
            body={"records": [{"error": "group not found", "httpCode": 404}]},
        )
        self.tokenize_api.with_raw_response.tokenize.side_effect = api_error

        response = self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1"]}]))

        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["error"], "group not found")
        self.assertEqual(response.errors[0]["code"], 404)
        self.assertEqual(response.errors[0]["request_id"], "req-3")

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.tokenize_api.with_raw_response.tokenize.return_value = fake_tokenize_raw_response([])

        self.vault.tokenize(TokenizeRequest(values=[{"value": "a@b.com", "token_group_names": ["g1"]}]))

        _, kwargs = self.tokenize_api.with_raw_response.tokenize.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")


if __name__ == "__main__":
    unittest.main()
