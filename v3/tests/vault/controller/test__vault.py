import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow.generated.rest.core import ApiError
from skyflow.vault.controller import FlowVaultController
from skyflow.vault.data import InsertRecord, InsertRequest, Upsert
from skyflow.utils.enums import UpsertType


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
        self.vault = FlowVaultController(self.vault_client)

    # ------------------------------------------------------------------ #
    # validation / initialization sequencing
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    def test_insert_validates_before_initializing_client(self, mock_validate):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1")

        self.vault.insert(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_insert_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.insert(InsertRequest(records=[], table="t1"))
        self.vault_client.initialize_client_configuration.assert_not_called()

    # ------------------------------------------------------------------ #
    # request -> wire field mapping
    # ------------------------------------------------------------------ #

    def test_maps_request_level_table_and_upsert(self):
        """When no record sets its own table/upsert, both go ONLY at the request level -- the
        vault rejects sending table_name/upsert in both places (see the validation tests), so
        the wire records must NOT also carry a resolved copy."""
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])
        request = InsertRequest(
            records=[InsertRecord(data={"a": 1})],
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
            records=[InsertRecord(data={"a": 1}, table="t2")],
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
            InsertRecord(data={"a": 1}, table="t2", upsert=Upsert(unique_columns=["b"])),
            InsertRecord(data={"a": 2}, table="t2"),
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
        request = InsertRequest(records=[InsertRecord(data={"a": 1}, table="t2")])  # no request-level table

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
            InsertRecord(
                data={"name": "saileshwar", "email": "nanana@gmail.com"},
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
        request = InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1")

        self.vault.insert(request)

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        self.assertNotIn("upsert", kwargs)
        self.assertIsNone(kwargs["records"][0].upsert)

    # ------------------------------------------------------------------ #
    # response shape -- mirrors Java's v3 InsertResponse (summary/success/errors)
    # ------------------------------------------------------------------ #

    def test_successful_records_go_to_success_list(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(
                skyflow_id="id1",
                tokens={"name": [{"token": "tok1", "tokenGroupName": "deterministic_string"}]},
                data={"name": "john doe"},
                table_name="table1",
            ),
        ], headers={"x-request-id": "req-1"})
        response = self.vault.insert(InsertRequest(records=[InsertRecord(data={"name": "john doe"})], table="table1"))

        self.assertEqual(response.summary["total_records"], 1)
        self.assertEqual(response.summary["total_inserted"], 1)
        self.assertEqual(response.summary["total_failed"], 0)
        self.assertEqual(len(response.success), 1)
        success = response.success[0]
        self.assertEqual(success["index"], 0)
        self.assertEqual(success["skyflow_id"], "id1")
        self.assertEqual(success["data"], {"name": "john doe"})
        self.assertEqual(success["table"], "table1")
        self.assertEqual(success["tokens"]["name"][0]["token"], "tok1")
        self.assertEqual(success["tokens"]["name"][0]["token_group_name"], "deterministic_string")
        self.assertEqual(response.errors, [])

    def test_mixed_success_and_error_records_are_split(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([
            FakeRecordResponseObject(skyflow_id="id1", tokens=None),
            FakeRecordResponseObject(error="bad row", http_code=400, table_name="t1"),
        ], headers={"x-request-id": "req-2"})
        response = self.vault.insert(InsertRequest(
            records=[InsertRecord(data={"a": 1}), InsertRecord(data={"a": 2})], table="t1",
        ))

        self.assertEqual(response.summary["total_records"], 2)
        self.assertEqual(response.summary["total_inserted"], 1)
        self.assertEqual(response.summary["total_failed"], 1)
        self.assertEqual(len(response.success), 1)
        self.assertEqual(response.success[0]["index"], 0)
        self.assertEqual(response.success[0]["skyflow_id"], "id1")
        self.assertEqual(len(response.errors), 1)
        self.assertEqual(response.errors[0]["index"], 1)
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
        response = self.vault.insert(InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1"))

        self.assertEqual(len(response.success), 1)
        self.assertEqual(response.errors, [])

    # ------------------------------------------------------------------ #
    # batching -- global index must stay continuous across batch boundaries
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, {"INSERT_BATCH_SIZE": "2"}, clear=False)
    def test_batches_at_the_configured_boundary(self):
        self.insert_api.with_raw_response.insert.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [InsertRecord(data={"a": i}) for i in range(3)]  # INSERT_BATCH_SIZE + 1

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

        self.assertEqual(self.insert_api.with_raw_response.insert.call_count, 2)
        call_sizes = [len(c.kwargs["records"]) for c in self.insert_api.with_raw_response.insert.call_args_list]
        self.assertEqual(sorted(call_sizes), [1, 2])
        self.assertEqual(len(response.success), 3)
        self.assertEqual(response.summary["total_records"], 3)
        self.assertEqual(response.summary["total_inserted"], 3)

    @patch.dict(os.environ, {"INSERT_BATCH_SIZE": "2"}, clear=False)
    def test_global_index_is_continuous_across_batches(self):
        """Regression pin: index is this record's position in the ORIGINAL records list, not
        reset to 0 at the start of each batch (mirrors Java's `batchNumber * batchSize` scheme)."""
        self.insert_api.with_raw_response.insert.side_effect = lambda **kwargs: FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id=f"id-{i}") for i in range(len(kwargs["records"]))]
        )
        records = [InsertRecord(data={"a": i}) for i in range(4)]

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

        self.assertEqual(sorted(s["index"] for s in response.success), [0, 1, 2, 3])

    @patch.dict(os.environ, {"INSERT_BATCH_SIZE": "50"}, clear=False)
    def test_records_under_batch_size_makes_a_single_call(self):
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse(
            [FakeRecordResponseObject(skyflow_id="id1")]
        )
        self.vault.insert(InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1"))
        self.insert_api.with_raw_response.insert.assert_called_once()

    # ------------------------------------------------------------------ #
    # transport failure -- isolate and continue
    # ------------------------------------------------------------------ #

    @patch.dict(os.environ, {"INSERT_BATCH_SIZE": "1"}, clear=False)
    def test_a_failing_batch_does_not_abort_remaining_batches(self):
        def side_effect(**kwargs):
            if kwargs["records"][0].data == {"a": 1}:
                raise Exception("network blip")
            return FakeRawResponse([FakeRecordResponseObject(skyflow_id="ok")])

        self.insert_api.with_raw_response.insert.side_effect = side_effect
        records = [InsertRecord(data={"a": 1}), InsertRecord(data={"a": 2})]

        response = self.vault.insert(InsertRequest(records=records, table="t1"))

        self.assertEqual(self.insert_api.with_raw_response.insert.call_count, 2)  # second batch still ran
        self.assertEqual(len(response.success), 1)
        self.assertEqual(len(response.errors), 1)
        self.assertIn("network blip", response.errors[0]["error"])
        self.assertEqual(response.errors[0]["index"], 0)  # first record, in the failing batch
        self.assertEqual(response.success[0]["index"], 1)

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

        response = self.vault.insert(InsertRequest(records=[InsertRecord(data={"name": "a"})], table="t1"))

        self.assertEqual(len(response.errors), 1)
        self.assertIn("notNull", response.errors[0]["error"])
        self.assertEqual(response.errors[0]["code"], 400)
        self.assertEqual(response.errors[0]["request_id"], "req-3")
        self.assertEqual(response.errors[0]["index"], 0)

    def test_api_error_with_flat_body_falls_back_to_one_error_per_record(self):
        api_error = ApiError(status_code=500, headers={}, body={"error": "internal error"})
        self.insert_api.with_raw_response.insert.side_effect = api_error

        response = self.vault.insert(InsertRequest(
            records=[InsertRecord(data={"a": 1}), InsertRecord(data={"a": 2})], table="t1",
        ))

        self.assertEqual(len(response.errors), 2)
        self.assertTrue(all(e["error"] == "internal error" for e in response.errors))
        self.assertTrue(all(e["code"] == 500 for e in response.errors))
        self.assertEqual([e["index"] for e in response.errors], [0, 1])

    # ------------------------------------------------------------------ #
    # per-call Authorization header injection
    # ------------------------------------------------------------------ #

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertEqual(headers.get("Authorization"), "Bearer the-current-token")

    def test_no_authorization_header_when_no_token_available(self):
        self.vault_client.get_current_bearer_token.return_value = None
        self.insert_api.with_raw_response.insert.return_value = FakeRawResponse([])

        self.vault.insert(InsertRequest(records=[InsertRecord(data={"a": 1})], table="t1"))

        _, kwargs = self.insert_api.with_raw_response.insert.call_args
        headers = kwargs["request_options"]["additional_headers"]
        self.assertNotIn("Authorization", headers)


if __name__ == "__main__":
    unittest.main()
