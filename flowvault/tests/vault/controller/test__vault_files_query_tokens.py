import base64
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from common.errors import SkyflowError
from skyflow.generated.rest.core import ApiError
from skyflow.utils.enums import CustomHeaderKey, FileUploadStatus
from skyflow.vault.controller import VaultController
from skyflow.vault.data import (
    QueryRequest,
    QueryOptions,
    GetTokensRequest,
    GetTokensRequestRecord,
    UploadFilesRequest,
    UploadFilesRequestRecord,
    UploadFilesRequestColumn,
    UploadFilesOptions,
    DeleteFilesRequest,
    DeleteFilesRequestRecord,
)


def fake_query_raw_response(records, metadata, headers=None):
    return SimpleNamespace(data=SimpleNamespace(records=records, metadata=metadata), headers=headers or {})


class FakeQueryRecord:
    def __init__(self, data):
        self.data = data


class FakeQueryMetadata:
    def __init__(self, columns):
        self.columns = columns


class FakeTokenizeResponseObject:
    def __init__(self, value=None, token_group_name=None, token=None, http_code=None, error=None):
        self.value = value
        self.token_group_name = token_group_name
        self.token = token
        self.http_code = http_code
        self.error = error


def fake_records_raw_response(records, headers=None):
    return SimpleNamespace(data=SimpleNamespace(records=records), headers=headers or {})


class FakeFileUploadResponseObject:
    def __init__(self, skyflow_id=None, table_name=None, data=None, error=None, http_code=None):
        self.skyflow_id = skyflow_id
        self.table_name = table_name
        self.data = data
        self.error = error
        self.http_code = http_code


class FakeFileDeleteResponseObject:
    def __init__(self, skyflow_id=None, table_name=None, data=None, error=None, http_code=None):
        self.skyflow_id = skyflow_id
        self.table_name = table_name
        self.data = data
        self.error = error
        self.http_code = http_code


class TestVaultQuery(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.query_api = MagicMock()
        self.vault_client.get_query_api.return_value = self.query_api
        self.vault = VaultController(self.vault_client)

    @patch("skyflow.vault.controller._vault.validate_query_request")
    def test_query_validates_before_initializing_client(self, mock_validate):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([], None)
        request = QueryRequest(query="SELECT a FROM t1")

        self.vault.query(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_query_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.query(QueryRequest(query="   "))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_maps_query_and_vault_id(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([], None)

        self.vault.query(QueryRequest(query="SELECT a FROM t1"))

        _, kwargs = self.query_api.with_raw_response.execute_query.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["query"], "SELECT a FROM t1")

    def test_maps_records_metadata_and_request_id(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response(
            [FakeQueryRecord({"name": "john"}), FakeQueryRecord({"name": "jane"})],
            FakeQueryMetadata(["name"]),
            headers={"x-request-id": "req-q"},
        )

        response = self.vault.query(QueryRequest(query="SELECT name FROM t1"))

        self.assertEqual([r.data for r in response.records], [{"name": "john"}, {"name": "jane"}])
        self.assertEqual(response.metadata.columns, ["name"])
        self.assertEqual(response.request_id, "req-q")

    def test_metadata_none_yields_none_metadata(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response(
            [FakeQueryRecord({"a": 1})], None,
        )

        response = self.vault.query(QueryRequest(query="SELECT a FROM t1"))

        self.assertIsNone(response.metadata)

    def test_transport_exception_raises_skyflow_error(self):
        self.query_api.with_raw_response.execute_query.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.query(QueryRequest(query="SELECT a FROM t1"))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_raises_with_status(self):
        self.query_api.with_raw_response.execute_query.side_effect = ApiError(
            status_code=400, headers={"x-request-id": "req-e"}, body={"error": "bad sql"},
        )
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.query(QueryRequest(query="SELECT a FROM t1"))
        self.assertEqual(ctx.exception.http_code, 400)

    def test_interceptor_adds_custom_header(self):
        self.query_api.with_raw_response.execute_query.return_value = fake_query_raw_response([], None)

        def interceptor(context):
            context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, "req-x")

        self.vault.query(QueryRequest(query="SELECT a FROM t1"), QueryOptions(interceptor=interceptor))

        _, kwargs = self.query_api.with_raw_response.execute_query.call_args
        self.assertEqual(kwargs["request_options"]["additional_headers"]["x-request-id"], "req-x")


class TestVaultGetTokens(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.tokens_api = MagicMock()
        self.vault_client.get_tokens_api.return_value = self.tokens_api
        self.vault = VaultController(self.vault_client)

    @patch("skyflow.vault.controller._vault.validate_get_tokens_request")
    def test_validates_before_initializing_client(self, mock_validate):
        self.tokens_api.with_raw_response.get_tokens.return_value = fake_records_raw_response([])
        request = GetTokensRequest(records=[GetTokensRequestRecord(value="v", token_group_name="g")])

        self.vault.get_tokens(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.get_tokens(GetTokensRequest(records=[]))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_maps_records(self):
        self.tokens_api.with_raw_response.get_tokens.return_value = fake_records_raw_response([])

        self.vault.get_tokens(GetTokensRequest(records=[
            GetTokensRequestRecord(value="v1", token_group_name="g1"),
            GetTokensRequestRecord(value="v2", token_group_name="g2"),
        ]))

        _, kwargs = self.tokens_api.with_raw_response.get_tokens.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(len(kwargs["records"]), 2)
        self.assertEqual(kwargs["records"][0].value, "v1")
        self.assertEqual(kwargs["records"][0].token_group_name, "g1")

    def test_success_and_error_records_in_one_list(self):
        self.tokens_api.with_raw_response.get_tokens.return_value = fake_records_raw_response([
            FakeTokenizeResponseObject(value="v1", token_group_name="g1", token="tok1", http_code=200),
            FakeTokenizeResponseObject(value="v2", token_group_name="g1", token=None, http_code=404, error="Token not found."),
        ], headers={"x-request-id": "req-t"})

        response = self.vault.get_tokens(GetTokensRequest(records=[
            GetTokensRequestRecord(value="v1", token_group_name="g1"),
            GetTokensRequestRecord(value="v2", token_group_name="g1"),
        ]))

        self.assertEqual(response.records[0].token, "tok1")
        self.assertIsNone(response.records[0].error)
        self.assertIsNone(response.records[0].request_id)
        self.assertEqual(response.records[1].error, "Token not found.")
        self.assertEqual(response.records[1].http_code, 404)
        self.assertEqual(response.records[1].request_id, "req-t")

    def test_transport_exception_raises_skyflow_error(self):
        self.tokens_api.with_raw_response.get_tokens.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.get_tokens(GetTokensRequest(records=[GetTokensRequestRecord(value="v", token_group_name="g")]))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        self.tokens_api.with_raw_response.get_tokens.side_effect = ApiError(
            status_code=404, headers={"x-request-id": "req-3"},
            body={"records": [{"error": "Token not found.", "httpCode": 404}]},
        )

        response = self.vault.get_tokens(GetTokensRequest(records=[GetTokensRequestRecord(value="v", token_group_name="g")]))
        self.assertEqual(response.records[0].error, "Token not found.")
        self.assertEqual(response.records[0].http_code, 404)
        self.assertEqual(response.records[0].request_id, "req-3")

    def test_injects_authorization_header_from_current_bearer_token(self):
        self.vault_client.get_current_bearer_token.return_value = "the-current-token"
        self.tokens_api.with_raw_response.get_tokens.return_value = fake_records_raw_response([])

        self.vault.get_tokens(GetTokensRequest(records=[GetTokensRequestRecord(value="v", token_group_name="g")]))

        _, kwargs = self.tokens_api.with_raw_response.get_tokens.call_args
        self.assertEqual(kwargs["request_options"]["additional_headers"].get("Authorization"), "Bearer the-current-token")


class TestVaultUploadFiles(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.files_api = MagicMock()
        self.vault_client.get_files_api.return_value = self.files_api
        self.put_status = 200
        self.put_calls = []

        def _capture_put(signed_url, content, content_type=None):
            data = content.read() if hasattr(content, "read") else content
            self.put_calls.append((signed_url, data, content_type))
            return SimpleNamespace(status_code=self.put_status)

        self.vault_client.put_signed_url.side_effect = _capture_put
        self.vault = VaultController(self.vault_client)
        self._tempfiles = []

    def tearDown(self):
        for path in self._tempfiles:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _make_file(self, content=b"filedata", suffix=".txt"):
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        self._tempfiles.append(path)
        return path

    def _ok_response(self, column="c", url="https://signed/url", skyflow_id="sid1", headers=None):
        return fake_records_raw_response(
            [FakeFileUploadResponseObject(skyflow_id=skyflow_id, table_name="t1", data={column: url}, http_code=200)],
            headers=headers,
        )

    @patch("skyflow.vault.controller._vault.validate_upload_files_request")
    def test_validates_before_initializing_client(self, mock_validate):
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()
        path = self._make_file()
        request = UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])])

        self.vault.upload_files(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.upload_files(UploadFilesRequest(records=[]))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_upload_via_file_path_success(self):
        path = self._make_file(b"filedata")
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response(headers={"x-request-id": "req-u"})

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        record = response.records[0]
        self.assertEqual(record.skyflow_id, "sid1")
        self.assertIsNone(record.error)
        self.assertIsNone(record.request_id)
        column = record.columns[0]
        self.assertEqual(column.column, "c")
        self.assertEqual(column.upload_status, FileUploadStatus.UPLOADED.value)
        self.assertEqual(column.file_name, os.path.basename(path))
        self.assertFalse(hasattr(column, "signed_url"))
        signed_url, data, _ = self.put_calls[0]
        self.assertEqual(signed_url, "https://signed/url")
        self.assertEqual(data, b"filedata")
        _, kwargs = self.files_api.with_raw_response.upload_files.call_args
        self.assertEqual(kwargs["records"][0].columns[0].file_name, os.path.basename(path))

    def test_upload_via_base64_success(self):
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()
        encoded = base64.b64encode(b"xyz").decode()

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", base64=encoded, file_name="doc.pdf")])]))

        self.assertEqual(response.records[0].columns[0].upload_status, FileUploadStatus.UPLOADED.value)
        self.assertEqual(self.put_calls[0][1], b"xyz")

    def test_upload_via_file_object_success(self):
        path = self._make_file(b"objbytes", suffix=".bin")
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        with open(path, "rb") as handle:
            response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
                table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_object=handle)])]))

        self.assertEqual(self.put_calls[0][1], b"objbytes")
        self.assertEqual(response.records[0].columns[0].file_name, os.path.basename(path))

    def test_content_type_inferred_from_file_name(self):
        path = self._make_file(suffix=".pdf")
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        args, _ = self.vault_client.put_signed_url.call_args
        self.assertEqual(args[2], "application/pdf")

    def test_per_record_error_marks_columns_skipped(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = fake_records_raw_response([
            FakeFileUploadResponseObject(skyflow_id=None, table_name="t1", data=None, error="bad record", http_code=400),
        ], headers={"x-request-id": "req-e"})

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        record = response.records[0]
        self.assertEqual(record.error, "bad record")
        self.assertEqual(record.request_id, "req-e")
        self.assertEqual(record.columns[0].upload_status, FileUploadStatus.SKIPPED.value)
        self.assertEqual(record.columns[0].error, "bad record")
        self.vault_client.put_signed_url.assert_not_called()

    def test_put_failure_marks_column_failed(self):
        self.put_status = 403
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        column = response.records[0].columns[0]
        self.assertEqual(column.upload_status, FileUploadStatus.FAILED.value)
        self.assertEqual(column.error, "PUT failed: 403")

    def test_put_exception_marks_column_failed(self):
        self.vault_client.put_signed_url.side_effect = Exception("conn reset")
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        column = response.records[0].columns[0]
        self.assertEqual(column.upload_status, FileUploadStatus.FAILED.value)
        self.assertIn("conn reset", column.error)

    def test_missing_signed_url_marks_column_skipped(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = fake_records_raw_response([
            FakeFileUploadResponseObject(skyflow_id="sid", table_name="t1", data={}, http_code=200),
        ])

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        self.assertEqual(response.records[0].columns[0].upload_status, FileUploadStatus.SKIPPED.value)
        self.vault_client.put_signed_url.assert_not_called()

    def test_skyflow_id_sent_when_provided(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", skyflow_id="existing", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        _, kwargs = self.files_api.with_raw_response.upload_files.call_args
        self.assertEqual(kwargs["records"][0].skyflow_id, "existing")

    def test_skyflow_id_omitted_when_absent(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))

        _, kwargs = self.files_api.with_raw_response.upload_files.call_args
        self.assertIsNone(kwargs["records"][0].skyflow_id)

    def test_file_not_found_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
                table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path="/no/such/file.xyz")])]))
        self.files_api.with_raw_response.upload_files.assert_not_called()

    def test_multiple_columns_all_uploaded(self):
        path_a = self._make_file(b"aaa")
        path_b = self._make_file(b"bbb")
        self.files_api.with_raw_response.upload_files.return_value = fake_records_raw_response([
            FakeFileUploadResponseObject(
                skyflow_id="sid1", table_name="t1",
                data={"c1": "https://signed/a", "c2": "https://signed/b"}, http_code=200),
        ])

        response = self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
            table_name="t1", columns=[
                UploadFilesRequestColumn(column="c1", file_path=path_a),
                UploadFilesRequestColumn(column="c2", file_path=path_b),
            ])]))

        statuses = {c.column: c.upload_status for c in response.records[0].columns}
        self.assertEqual(statuses, {"c1": FileUploadStatus.UPLOADED.value, "c2": FileUploadStatus.UPLOADED.value})
        self.assertEqual(len(self.put_calls), 2)
        self.assertEqual({data for _, data, _ in self.put_calls}, {b"aaa", b"bbb"})

    def test_invalid_base64_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
                table_name="t1", columns=[UploadFilesRequestColumn(column="c", base64="!!!not-base64!!!", file_name="x.bin")])]))
        self.files_api.with_raw_response.upload_files.assert_not_called()

    def test_whole_call_error_raises(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.side_effect = ApiError(
            status_code=401, headers={}, body={"error": "unauthorized"})
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.upload_files(UploadFilesRequest(records=[UploadFilesRequestRecord(
                table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]))
        self.assertEqual(ctx.exception.http_code, 401)

    def test_interceptor_adds_custom_header(self):
        path = self._make_file()
        self.files_api.with_raw_response.upload_files.return_value = self._ok_response()

        def interceptor(context):
            context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, "req-x")

        self.vault.upload_files(
            UploadFilesRequest(records=[UploadFilesRequestRecord(
                table_name="t1", columns=[UploadFilesRequestColumn(column="c", file_path=path)])]),
            UploadFilesOptions(interceptor=interceptor),
        )

        _, kwargs = self.files_api.with_raw_response.upload_files.call_args
        self.assertEqual(kwargs["request_options"]["additional_headers"]["x-request-id"], "req-x")


class TestVaultDeleteFiles(unittest.TestCase):
    def setUp(self):
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "vault123"
        self.vault_client.get_logger.return_value = Mock()
        self.vault_client.get_current_bearer_token.return_value = None
        self.files_api = MagicMock()
        self.vault_client.get_files_api.return_value = self.files_api
        self.vault = VaultController(self.vault_client)

    @patch("skyflow.vault.controller._vault.validate_delete_files_request")
    def test_validates_before_initializing_client(self, mock_validate):
        self.files_api.with_raw_response.delete_files.return_value = fake_records_raw_response([])
        request = DeleteFilesRequest(records=[DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1")])

        self.vault.delete_files(request)

        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.vault_client.initialize_client_configuration.assert_called_once()

    def test_raises_for_invalid_request(self):
        with self.assertRaises(SkyflowError):
            self.vault.delete_files(DeleteFilesRequest(records=[]))
        self.vault_client.initialize_client_configuration.assert_not_called()

    def test_maps_by_skyflow_id(self):
        self.files_api.with_raw_response.delete_files.return_value = fake_records_raw_response([])

        self.vault.delete_files(DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c1", "c2"], skyflow_id="id1"),
        ]))

        _, kwargs = self.files_api.with_raw_response.delete_files.call_args
        self.assertEqual(kwargs["vault_id"], "vault123")
        self.assertEqual(kwargs["records"][0].table_name, "t1")
        self.assertEqual(kwargs["records"][0].columns, ["c1", "c2"])
        self.assertEqual(kwargs["records"][0].skyflow_id, "id1")

    def test_maps_by_unique_values(self):
        self.files_api.with_raw_response.delete_files.return_value = fake_records_raw_response([])

        self.vault.delete_files(DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], unique_values=[{"email": "a@b.com"}]),
        ]))

        _, kwargs = self.files_api.with_raw_response.delete_files.call_args
        self.assertEqual(kwargs["records"][0].unique_values[0].data, {"email": "a@b.com"})

    def test_success_record_maps_column_statuses(self):
        self.files_api.with_raw_response.delete_files.return_value = fake_records_raw_response([
            FakeFileDeleteResponseObject(
                skyflow_id="id1", table_name="t1",
                data={"c1": {"status": "DELETED"}, "c2": {"status": "DELETED"}}, http_code=200),
        ], headers={"x-request-id": "req-d"})

        response = self.vault.delete_files(DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c1", "c2"], skyflow_id="id1"),
        ]))

        record = response.records[0]
        self.assertEqual(record.skyflow_id, "id1")
        self.assertIsNone(record.error)
        self.assertIsNone(record.request_id)
        self.assertEqual([(c.column, c.status) for c in record.columns], [("c1", "DELETED"), ("c2", "DELETED")])

    def test_failed_record_has_none_columns(self):
        self.files_api.with_raw_response.delete_files.return_value = fake_records_raw_response([
            FakeFileDeleteResponseObject(skyflow_id="bad", table_name="t1", data=None, error="invalid", http_code=404),
        ], headers={"x-request-id": "req-f"})

        response = self.vault.delete_files(DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="bad"),
        ]))

        record = response.records[0]
        self.assertIsNone(record.columns)
        self.assertEqual(record.error, "invalid")
        self.assertEqual(record.http_code, 404)
        self.assertEqual(record.request_id, "req-f")

    def test_transport_exception_raises_skyflow_error(self):
        self.files_api.with_raw_response.delete_files.side_effect = Exception("network blip")
        with self.assertRaises(SkyflowError) as ctx:
            self.vault.delete_files(DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1")]))
        self.assertIn("network blip", ctx.exception.message)

    def test_api_error_with_per_record_body_returns_error_row(self):
        self.files_api.with_raw_response.delete_files.side_effect = ApiError(
            status_code=404, headers={"x-request-id": "req-3"},
            body={"records": [{"error": "invalid", "httpCode": 404}]},
        )

        response = self.vault.delete_files(DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1")]))
        self.assertEqual(response.records[0].error, "invalid")
        self.assertEqual(response.records[0].request_id, "req-3")


if __name__ == "__main__":
    unittest.main()
