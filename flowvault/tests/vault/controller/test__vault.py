import unittest
from unittest.mock import MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.vault.controller import VaultController
from skyflow_flowvault.vault.data import InsertRequest, Upsert
from skyflow_flowvault.utils.enums import UpsertType


class FakeRecordResponseObject:
    def __init__(self, skyflow_id=None, tokens=None, data=None, error=None, http_code=None, table_name=None):
        self.skyflow_id = skyflow_id
        self.tokens = tokens
        self.data = data
        self.error = error
        self.http_code = http_code
        self.table_name = table_name


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
        self.vault_client.get_insert_api.return_value = self.insert_api
        self.vault = VaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow_flowvault.vault.controller._vault.validate_insert_request")
    def test_insert_validates_before_initializing_client(self, mock_validate):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(records=[dict(values={"a": 1})], table="t1")

        self.vault.insert(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_insert_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[], table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # shared BaseVaultController validation helpers, exercised end-to-end via insert()
    # (unit-tested in isolation in common/tests/vault/test_base_vault_controller.py)
    # ------------------------------------------------------------------ #

    def test_insert_raises_on_empty_key(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values={"": "value"})], table="t1"))
        self.insert_api.with_raw_response.insert.assert_not_called()

    def test_insert_raises_on_empty_value(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values={"a": ""})], table="t1"))
        self.insert_api.with_raw_response.insert.assert_not_called()

    def test_insert_raises_on_non_dict_values(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values=["not", "a", "dict"])], table="t1"))

    def test_insert_raises_on_empty_values_dict(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values={})], table="t1"))

    def test_insert_raises_on_invalid_request_level_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values={"a": 1})], table="   "))

    def test_insert_raises_on_invalid_per_record_table_name(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[dict(values={"a": 1}, table="   ")]))

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table_and_upsert(self):
        """When no record sets its own table/upsert, both go ONLY at the request level -- the
        vault rejects sending table_name/upsert in both places (see the validation tests), so
        the wire records must NOT also carry a resolved copy."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(
            records=[dict(values={"a": 1})],
            table="t1",
            upsert=Upsert(update_type=UpsertType.REPLACE, unique_columns=["a"]),
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
            records=[dict(values={"a": 1}, table="t2")],
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
        request = InsertRequest(records=[
            dict(values={"a": 1}, table="t2", upsert=Upsert(unique_columns=["b"])),
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
        request = InsertRequest(records=[dict(values={"a": 1}, table="t2")])  # no request-level table

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("table_name", kwargs)

    def test_wire_shape_matches_confirmed_working_request(self):
        """Regression pin for a real bug: a request with only per-record table/upsert (no
        request-level table/upsert at all) previously sent explicit `"tableName": null` /
        `"upsert": null` at the top level, which diverged from a hand-verified working request
        against a real vault (confirmed to have neither key present when unset)."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(records=[
            dict(
                values={"name": "saileshwar", "email": "nanana@gmail.com"},
                table="table1",
                upsert=Upsert(update_type=UpsertType.UPDATE, unique_columns=["email"]),
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
        request = InsertRequest(records=[dict(values={"a": 1})], table="t1")

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
        response = self.vault.insert(InsertRequest(records=[dict(values={"name": "john doe"})], table="table1"))

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
        response = self.vault.insert(InsertRequest(records=[dict(values={"email": "a@b.com"})], table="t1"))

        self.assertEqual(response.inserted_fields[0]["email"], ["tok-det", "tok-nondet"])

    def test_mixed_success_and_error_records_are_split(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(skyflow_id="id1", tokens=None),
            FakeRecordResponseObject(error="bad row", http_code=400, table_name="t1"),
        ], headers={"x-request-id": "req-2"})
        response = self.vault.insert(InsertRequest(
            records=[dict(values={"a": 1}), dict(values={"a": 2})], table="t1",
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
        response = self.vault.insert(InsertRequest(records=[dict(values={"a": 1})], table="t1"))

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

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

        self.insert_api.with_raw_response.insert.assert_called_once()
        call_size = len(self.insert_api.with_raw_response.insert.call_args.kwargs["records"])
        self.assertEqual(call_size, 4)
        self.assertEqual(len(response.inserted_fields), 4)

    def test_request_index_matches_position_in_the_original_records_list(self):
        self.insert_api.with_raw_response.insert.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [dict(values={"a": i}) for i in range(4)]

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

        self.assertEqual(sorted(s["request_index"] for s in response.inserted_fields), [0, 1, 2, 3])

    # ------------------------------------------------------------------ #
    # transport failure
    # ------------------------------------------------------------------ #

    def test_transport_exception_marks_every_record_as_an_error(self):
        """Without batching, one API call carries every record -- a transport-level exception
        on that single call means every record in the request fails, not just some."""
        self.insert_api.with_raw_response.insert.side_effect = Exception("network blip")
        records = [dict(values={"a": 1}), dict(values={"a": 2})]

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

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

        response = self.vault.insert(InsertRequest(records=[dict(values={"name": "a"})], table="t1"))

        self.assertEqual(len(response.errors), 1)
        self.assertIn("notNull", response.errors[0]["error"])
        self.assertEqual(response.errors[0]["code"], 400)
        self.assertEqual(response.errors[0]["request_id"], "req-3")
        self.assertEqual(response.errors[0]["request_index"], 0)

    def test_api_error_with_flat_body_falls_back_to_one_error_per_record(self):
        api_error = ApiError(status_code=500, headers={}, body={"error": "internal error"})
        self.insert_api.with_raw_response.insert.side_effect = api_error

        response = self.vault.insert(InsertRequest(
            records=[dict(values={"a": 1}), dict(values={"a": 2})], table="t1",
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

        self.vault.insert(InsertRequest(records=[dict(values={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")

    def test_no_authorization_header_when_no_token_available(self):
        self.vault_client.get_current_bearer_token.return_value = None
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(records=[dict(values={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertNotIn("Authorization", headers)


if __name__ == "__main__":
    unittest.main()
