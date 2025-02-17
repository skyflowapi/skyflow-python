import unittest
from unittest.mock import patch, Mock
import os
import json
from unittest.mock import MagicMock
from urllib.parse import quote
from requests import PreparedRequest
from requests.models import HTTPError
from skyflow.error import SkyflowError
from skyflow.utils import get_credentials, SkyflowMessages, get_vault_url, construct_invoke_connection_request, \
    parse_insert_response, parse_update_record_response, parse_delete_response, parse_get_response, \
    parse_detokenize_response, parse_tokenize_response, parse_query_response, parse_invoke_connection_response, \
    handle_exception, validate_api_key, encode_column_values
from skyflow.utils._utils import parse_path_params, to_lowercase_keys, get_metrics
from skyflow.utils.enums import EnvUrls, Env, ContentType
from skyflow.vault.connection import InvokeConnectionResponse
from skyflow.vault.data import InsertResponse, DeleteResponse, GetResponse, QueryResponse
from skyflow.vault.tokens import DetokenizeResponse, TokenizeResponse

creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
with open(creds_path, 'r') as file:
    credentials = json.load(file)

TEST_ERROR_MESSAGE = "Test error message."
VALID_ENV_CREDENTIALS = credentials

class TestUtils(unittest.TestCase):

    @patch.dict(os.environ, {"SKYFLOW_CREDENTIALS": json.dumps(VALID_ENV_CREDENTIALS)})
    def test_get_credentials_env_variable(self):
        credentials = get_credentials()
        credentials_string = credentials.get('credentials_string')
        self.assertEqual(credentials_string, json.dumps(VALID_ENV_CREDENTIALS).replace('\n', '\\n'))

    def test_get_credentials_with_config_level_creds(self):
        test_creds = {"authToken": "test_token"}
        creds = get_credentials(config_level_creds=test_creds)
        self.assertEqual(creds, test_creds)

    def test_get_credentials_with_common_creds(self):
        test_creds = {"authToken": "test_token"}
        creds = get_credentials(common_skyflow_creds=test_creds)
        self.assertEqual(creds, test_creds)

    def test_get_vault_url_valid(self):
        valid_cluster_id = "testCluster"
        valid_env = Env.DEV
        valid_vault_id = "vault123"
        url = get_vault_url(valid_cluster_id, valid_env, valid_vault_id)
        expected_url = f"https://{valid_cluster_id}.vault.skyflowapis.dev"
        self.assertEqual(url, expected_url)

    def test_get_vault_url_with_invalid_cluster_id(self):
        valid_cluster_id = ""
        valid_env = Env.DEV
        valid_vault_id = "vault123"
        with self.assertRaises(SkyflowError) as context:
            url = get_vault_url(valid_cluster_id, valid_env, valid_vault_id)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format(valid_vault_id))

    def test_get_vault_url_with_invalid_env(self):
        valid_cluster_id = "cluster_id"
        valid_env =EnvUrls.DEV
        valid_vault_id = "vault123"
        with self.assertRaises(SkyflowError) as context:
            url = get_vault_url(valid_cluster_id, valid_env, valid_vault_id)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_ENV.value.format(valid_vault_id))

    def test_parse_path_params(self):
        url = "https://example.com/{param1}/{param2}"
        path_params = {"param1": "value1", "param2": "value2"}
        parsed_url = parse_path_params(url, path_params)
        self.assertEqual(parsed_url, "https://example.com/value1/value2")

    def test_to_lowercase_keys(self):
        input_dict = {"Key1": "value1", "KEY2": "value2"}
        expected_output = {"key1": "value1", "key2": "value2"}
        self.assertEqual(to_lowercase_keys(input_dict), expected_output)

    def test_get_metrics(self):
        metrics = get_metrics()
        self.assertIn('sdk_name_version', metrics)
        self.assertIn('sdk_client_device_model', metrics)
        self.assertIn('sdk_client_os_details', metrics)
        self.assertIn('sdk_runtime_details', metrics)


    def test_construct_invoke_connection_request_valid(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)

        expected_url = parse_path_params(connection_url, mock_connection_request.path_params) + "?query=test"
        self.assertEqual(result.url, expected_url)

        self.assertEqual(result.method, "POST")
        self.assertEqual(result.headers['Content-Type'], ContentType.JSON.value)

        self.assertEqual(result.body, json.dumps(mock_connection_request.body))

    def test_construct_invoke_connection_request_with_invalid_headers(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = []
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        with self.assertRaises(SkyflowError) as context:
            result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value)

    def test_construct_invoke_connection_request_with_invalid_request_method(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        with self.assertRaises(SkyflowError) as context:
            result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_METHOD.value)

    def test_construct_invoke_connection_request_with_invalid_request_body(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = []
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"
        with self.assertRaises(SkyflowError) as context:
            result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)

    def test_construct_invoke_connection_request_with_url_encoded_content_type(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = {"Content-Type": ContentType.URLENCODED.value}
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)

    def test_construct_invoke_connection_request_with_form_date_content_type(self):
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = {"Content-Type": ContentType.FORMDATA.value}
        mock_connection_request.body = {
            "name": (None, "John Doe")
        }
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)

    def test_parse_insert_response(self):
        api_response = Mock()

        api_response.raw_data = json.dumps({
            "responses": [
                {"Status": 200, "Body": {"records": [{"skyflow_id": "id1"}]}},
                {"Status": 400, "Body": {"error": "TEST_ERROR_MESSAGE"}}
            ]
        }).encode('utf-8')

        api_response.headers = {"x-request-id": "test-request-id"}

        result = parse_insert_response(api_response, continue_on_error=True)

        self.assertEqual(len(result.inserted_fields), 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.inserted_fields[0]['skyflow_id'], "id1")
        self.assertEqual(result.errors[0]['error'], "TEST_ERROR_MESSAGE")
        self.assertEqual(result.errors[0]['request_id'], "test-request-id")

    def test_parse_insert_response_continue_on_error_false(self):
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(skyflow_id="id_1", tokens={"token1": "token_value1"}),
            Mock(skyflow_id="id_2", tokens={"token2": "token_value2"})
        ]

        result = parse_insert_response(mock_api_response, continue_on_error=False)

        self.assertIsInstance(result, InsertResponse)

        expected_inserted_fields = [
            {"skyflow_id": "id_1", "token1": "token_value1"},
            {"skyflow_id": "id_2", "token2": "token_value2"}
        ]
        self.assertEqual(result.inserted_fields, expected_inserted_fields)

        self.assertEqual(result.errors, [])

    def test_parse_update_record_response(self):
        api_response = Mock()
        api_response.skyflow_id = "id1"
        api_response.tokens = {"token1": "value1"}
        result = parse_update_record_response(api_response)
        self.assertEqual(result.updated_field['skyflow_id'], "id1")
        self.assertEqual(result.updated_field['token1'], "value1")

    def test_parse_delete_response_successful(self):
        mock_api_response = Mock()
        mock_api_response.record_id_response = ["id_1", "id_2", "id_3"]

        result = parse_delete_response(mock_api_response)

        self.assertIsInstance(result, DeleteResponse)

        expected_deleted_ids = ["id_1", "id_2", "id_3"]
        self.assertEqual(result.deleted_ids, expected_deleted_ids)

        self.assertEqual(result.errors, [])

    def test_parse_get_response_successful(self):
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(fields={'field1': 'value1', 'field2': 'value2'}),
            Mock(fields={'field1': 'value3', 'field2': 'value4'})
        ]

        result = parse_get_response(mock_api_response)

        self.assertIsInstance(result, GetResponse)

        expected_data = [
            {'field1': 'value1', 'field2': 'value2'},
            {'field1': 'value3', 'field2': 'value4'}
        ]
        self.assertEqual(result.data, expected_data)

        self.assertEqual(result.errors, [])

    def test_parse_detokenize_response_with_mixed_records(self):
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(token="token1", value="value1", value_type=Mock(value="Type1"), error=None),
            Mock(token="token2", value=None, value_type=None, error="Some error"),
            Mock(token="token3", value="value3", value_type=Mock(value="Type2"), error=None),
        ]

        result = parse_detokenize_response(mock_api_response)
        self.assertIsInstance(result, DetokenizeResponse)

        expected_detokenized_fields = [
            {"token": "token1", "value": "value1", "type": "Type1"},
            {"token": "token3", "value": "value3", "type": "Type2"}
        ]

        expected_errors = [
            {"token": "token2", "error": "Some error"}
        ]

        self.assertEqual(result.detokenized_fields, expected_detokenized_fields)
        self.assertEqual(result.errors, expected_errors)

    def test_parse_tokenize_response_with_valid_records(self):
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(token="token1"),
            Mock(token="token2"),
            Mock(token="token3"),
        ]

        result = parse_tokenize_response(mock_api_response)
        self.assertIsInstance(result, TokenizeResponse)

        expected_tokenized_fields = [
            {"token": "token1"},
            {"token": "token2"},
            {"token": "token3"}
        ]

        self.assertEqual(result.tokenized_fields, expected_tokenized_fields)

    def test_parse_query_response_with_valid_records(self):
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(fields={"field1": "value1", "field2": "value2"}),
            Mock(fields={"field1": "value3", "field2": "value4"})
        ]

        result = parse_query_response(mock_api_response)

        self.assertIsInstance(result, QueryResponse)

        expected_fields = [
            {"field1": "value1", "field2": "value2", "tokenized_data": {}},
            {"field1": "value3", "field2": "value4", "tokenized_data": {}}
        ]

        self.assertEqual(result.fields, expected_fields)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_successful(self, mock_response):
        mock_response.status_code = 200
        mock_response.content = json.dumps({"key": "value"}).encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.response["key"], "value")
        self.assertEqual(result.response["request_id"], "1234")

    @patch("requests.Response")
    def test_parse_invoke_connection_response_json_decode_error(self, mock_response):

        mock_response.status_code = 200
        mock_response.content = "Non-JSON Content".encode('utf-8')

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.RESPONSE_NOT_JSON.value.format("Non-JSON Content"))

    @patch("requests.Response")
    def test_parse_invoke_connection_response_http_error_with_json_error_message(self, mock_response):
        mock_response.status_code = 404
        mock_response.content = json.dumps({"error": {"message": "Not Found"}}).encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}

        mock_response.raise_for_status.side_effect = HTTPError("404 Error")

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, "Not Found - request id: 1234")

    @patch("requests.Response")
    def test_parse_invoke_connection_response_http_error_without_json_error_message(self, mock_response):
        mock_response.status_code = 500
        mock_response.content = "Internal Server Error".encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}

        mock_response.raise_for_status.side_effect = HTTPError("500 Error")

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.RESPONSE_NOT_JSON.value.format("Internal Server Error") + " - request id: 1234")

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_json_error(self, mock_log_and_reject_error):

        mock_error = Mock()
        mock_error.headers = {
            'x-request-id': '1234',
            'content-type': 'application/json'
        }
        mock_error.body = json.dumps({
            "error": {
                "message": "JSON error occurred.",
                "http_code": 400,
                "http_status": "Bad Request",
                "grpc_code": "8",
                "details": "Detailed message"
            }
        }).encode('utf-8')
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "JSON error occurred.",
            400,
            "1234",
            "Bad Request",
            "8",
            "Detailed message",
            logger=mock_logger
        )

    def test_validate_api_key_valid_key(self):
        valid_key = "sky-ABCDE-1234567890abcdef1234567890abcdef"
        self.assertTrue(validate_api_key(valid_key))

    def test_validate_api_key_invalid_length(self):
        invalid_key = "sky-ABCDE-123"
        self.assertFalse(validate_api_key(invalid_key))

    def test_validate_api_key_invalid_pattern(self):
        invalid_key = "sky-ABCDE-1234567890GHIJKL7890abcdef"
        self.assertFalse(validate_api_key(invalid_key))

    def test_encode_column_values(self):
        get_request = MagicMock()
        get_request.column_values = ["Hello World!", "foo/bar", "key=value", "email@example.com"]

        expected_encoded_values = [
            quote("Hello World!"),
            quote("foo/bar"),
            quote("key=value"),
            quote("email@example.com"),
        ]

        result = encode_column_values(get_request)
        self.assertEqual(result, expected_encoded_values)
