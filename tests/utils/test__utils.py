import unittest
from unittest.mock import patch, Mock
import os
import json
from unittest.mock import MagicMock
from urllib.parse import quote
from requests import PreparedRequest
from requests.models import HTTPError
from skyflow.error import SkyflowError
from skyflow.generated.rest import ErrorResponse
from skyflow.utils import get_credentials, SkyflowMessages, get_vault_url, construct_invoke_connection_request, \
    parse_insert_response, parse_update_record_response, parse_delete_response, parse_get_response, \
    parse_detokenize_response, parse_tokenize_response, parse_query_response, parse_invoke_connection_response, \
    handle_exception, validate_api_key, encode_column_values, parse_deidentify_text_response, \
    parse_reidentify_text_response, convert_detected_entity_to_entity_info
from skyflow.utils._utils import parse_path_params, to_lowercase_keys, get_metrics, handle_json_error
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

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_with_dict_data(self, mock_log_and_reject_error):
        """Test handling JSON error when data is already a dict."""
        error_dict = {
            "error": {
                "message": "Dict error message",
                "http_code": 400,
                "http_status": "Bad Request",
                "grpc_code": 3,
                "details": ["detail1"]
            }
        }

        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id"

        handle_json_error(mock_error, error_dict, request_id, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "Dict error message",
            400,
            request_id,
            "Bad Request",
            3,
            ["detail1"],
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_with_error_response_object(self, mock_log_and_reject_error):
        """Test handling JSON error when data is an ErrorResponse object."""
        mock_error_response = Mock(spec=ErrorResponse)
        mock_error_response.dict.return_value = {
            "error": {
                "message": "ErrorResponse message",
                "http_code": 403,
                "http_status": "Forbidden",
                "grpc_code": 7,
                "details": ["detail2"]
            }
        }

        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id-2"

        handle_json_error(mock_error, mock_error_response, request_id, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "ErrorResponse message",
            403,
            request_id,
            "Forbidden",
            7,
            ["detail2"],
            logger=mock_logger
        )

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
        api_response.headers = {"x-request-id": "12345", "content-type": "application/json"}
        api_response.data = Mock(responses=[
            {"Status": 200, "Body": {"records": [{"skyflow_id": "id1"}]}},
            {"Status": 400, "Body": {"error": TEST_ERROR_MESSAGE}}
        ])
        result = parse_insert_response(api_response, continue_on_error=True)
        self.assertEqual(len(result.inserted_fields), 1)
        self.assertEqual(len(result.errors), 1)
        # Assert first successful record
        self.assertEqual(result.inserted_fields[0]["skyflow_id"], "id1")
        # Assert error record
        self.assertEqual(result.errors[0]["error"], TEST_ERROR_MESSAGE)
        self.assertEqual(result.errors[0]["http_code"], 400)
        self.assertEqual(result.errors[0]["request_id"], "12345")

    def test_parse_insert_response_continue_on_error_false(self):
        mock_api_response = Mock()
        mock_api_response.headers = {"x-request-id": "12345", "content-type": "application/json"}
        mock_api_response.data = Mock(records=[
            Mock(skyflow_id="id_1", tokens={"token1": "token_value1"}),
            Mock(skyflow_id="id_2", tokens={"token2": "token_value2"})
        ])
        result = parse_insert_response(mock_api_response, continue_on_error=False)

        self.assertIsInstance(result, InsertResponse)

        expected_inserted_fields = [
            {"skyflow_id": "id_1", "token1": "token_value1"},
            {"skyflow_id": "id_2", "token2": "token_value2"}
        ]
        self.assertEqual(result.inserted_fields, expected_inserted_fields)

        self.assertEqual(result.errors, None)

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

        self.assertEqual(result.errors, None)

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

        # self.assertEqual(result.errors, None)

    def test_parse_detokenize_response_with_mixed_records(self):
        mock_api_response = Mock()
        mock_api_response.headers = {"x-request-id": "12345", "content-type": "application/json"}
        mock_api_response.data = Mock(records=[
            Mock(token="token1", value="value1", value_type="Type1", error=None),
            Mock(token="token2", value=None, value_type=None, error="Some error"),
            Mock(token="token3", value="value3", value_type="Type2", error=None),     
        ])

        result = parse_detokenize_response(mock_api_response)
        self.assertIsInstance(result, DetokenizeResponse)

        expected_detokenized_fields = [
            {"token": "token1", "value": "value1", "type": "Type1"},
            {"token": "token3", "value": "value3", "type": "Type2"}
        ]

        expected_errors = [
            {"token": "token2", "error": "Some error", "request_id": "12345"}
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
        self.assertEqual(result.data["key"], "value")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertEqual(result.errors, None)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_json_decode_error(self, mock_response):
        """Test that non-JSON content in successful response is returned as string."""
        mock_response.status_code = 200
        mock_response.content = "Non-JSON Content".encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "Non-JSON Content")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_http_error_with_json_error_message(self, mock_response):
        mock_response.status_code = 404
        mock_response.content = json.dumps({"error": {"message": "Not Found"}}).encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}

        mock_response.raise_for_status.side_effect = HTTPError("404 Error")

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, "Not Found")
        self.assertEqual(context.exception.request_id, "1234")

    @patch("requests.Response")
    def test_parse_invoke_connection_response_http_error_without_json_error_message(self, mock_response):
        mock_response.status_code = 500
        mock_response.content = "Internal Server Error".encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}

        mock_response.raise_for_status.side_effect = HTTPError("500 Error")

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, "Internal Server Error")
        self.assertEqual(context.exception.http_code, 500)
        self.assertEqual(context.exception.request_id, "1234")

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

    def test_parse_deidentify_text_response(self):
        """Test parsing deidentify text response with multiple entities."""
        mock_entity = Mock()
        mock_entity.token = "token123"
        mock_entity.value = "sensitive_value"
        mock_entity.entity_type = "EMAIL"
        mock_entity.entity_scores = {"EMAIL": 0.95}
        mock_entity.location = Mock(
            start_index=10,
            end_index=20,
            start_index_processed=15,
            end_index_processed=25
        )

        mock_api_response = Mock()
        mock_api_response.processed_text = "Sample processed text"
        mock_api_response.entities = [mock_entity]
        mock_api_response.word_count = 3
        mock_api_response.character_count = 20

        result = parse_deidentify_text_response(mock_api_response)

        self.assertEqual(result.processed_text, "Sample processed text")
        self.assertEqual(result.word_count, 3)
        self.assertEqual(result.char_count, 20)
        self.assertEqual(len(result.entities), 1)

        entity = result.entities[0]
        self.assertEqual(entity.token, "token123")
        self.assertEqual(entity.value, "sensitive_value")
        self.assertEqual(entity.entity, "EMAIL")
        self.assertEqual(entity.scores, {"EMAIL": 0.95})
        self.assertEqual(entity.text_index.start, 10)
        self.assertEqual(entity.text_index.end, 20)
        self.assertEqual(entity.processed_index.start, 15)
        self.assertEqual(entity.processed_index.end, 25)

    def test_parse_deidentify_text_response_no_entities(self):
        """Test parsing deidentify text response with no entities."""
        mock_api_response = Mock()
        mock_api_response.processed_text = "Sample processed text"
        mock_api_response.entities = []
        mock_api_response.word_count = 3
        mock_api_response.character_count = 20

        result = parse_deidentify_text_response(mock_api_response)

        self.assertEqual(result.processed_text, "Sample processed text")
        self.assertEqual(result.word_count, 3)
        self.assertEqual(result.char_count, 20)
        self.assertEqual(len(result.entities), 0)

    def test_parse_reidentify_text_response(self):
        """Test parsing reidentify text response."""
        mock_api_response = Mock()
        mock_api_response.text = "Reidentified text with actual values"

        result = parse_reidentify_text_response(mock_api_response)

        self.assertEqual(result.processed_text, "Reidentified text with actual values")

    def test__convert_detected_entity_to_entity_info(self):
        """Test converting detected entity to EntityInfo object."""
        mock_detected_entity = Mock()
        mock_detected_entity.token = "token123"
        mock_detected_entity.value = "sensitive_value"
        mock_detected_entity.entity_type = "EMAIL"
        mock_detected_entity.entity_scores = {"EMAIL": 0.95}
        mock_detected_entity.location = Mock(
            start_index=10,
            end_index=20,
            start_index_processed=15,
            end_index_processed=25
        )

        result = convert_detected_entity_to_entity_info(mock_detected_entity)

        self.assertEqual(result.token, "token123")
        self.assertEqual(result.value, "sensitive_value")
        self.assertEqual(result.entity, "EMAIL")
        self.assertEqual(result.scores, {"EMAIL": 0.95})
        self.assertEqual(result.text_index.start, 10)
        self.assertEqual(result.text_index.end, 20)
        self.assertEqual(result.processed_index.start, 15)
        self.assertEqual(result.processed_index.end, 25)

    def test__convert_detected_entity_to_entity_info_with_minimal_data(self):
        """Test converting detected entity with minimal required data."""
        mock_detected_entity = Mock()
        mock_detected_entity.token = "token123"
        mock_detected_entity.value = None
        mock_detected_entity.entity_type = "UNKNOWN"
        mock_detected_entity.entity_scores = {}
        mock_detected_entity.location = Mock(
            start_index=0,
            end_index=0,
            start_index_processed=0,
            end_index_processed=0
        )

        result = convert_detected_entity_to_entity_info(mock_detected_entity)

        self.assertEqual(result.token, "token123")
        self.assertIsNone(result.value)
        self.assertEqual(result.entity, "UNKNOWN")
        self.assertEqual(result.scores, {})
        self.assertEqual(result.text_index.start, 0)
        self.assertEqual(result.text_index.end, 0)
        self.assertEqual(result.processed_index.start, 0)
        self.assertEqual(result.processed_index.end, 0)


    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_connect_error(self, mock_log_and_reject_error):
        """Test handling httpx.ConnectError."""
        import httpx
        mock_error = httpx.ConnectError("Connection refused")
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            SkyflowMessages.Error.GENERIC_API_ERROR.value,
            SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
            None,
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_no_headers_attribute(self, mock_log_and_reject_error):
        """Test handling error without headers attribute."""
        mock_error = Exception("Generic error")
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "Generic error",
            SkyflowMessages.ErrorCodes.SERVER_ERROR.value,
            None,
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_no_body_attribute(self, mock_log_and_reject_error):
        """Test handling error without body attribute."""
        mock_error = Mock()
        mock_error.headers = {"x-request-id": "12345"}
        delattr(mock_error, 'body')
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once()
        self.assertEqual(
            mock_log_and_reject_error.call_args[0][1],
            SkyflowMessages.ErrorCodes.SERVER_ERROR.value
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_text_plain_error(self, mock_log_and_reject_error):
        """Test handling text/plain content type error."""
        mock_error = Mock()
        mock_error.headers = {
            'x-request-id': '1234',
            'content-type': 'text/plain'
        }
        mock_error.body = "Plain text error message"
        mock_error.status = 500
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "Plain text error message",
            500,
            "1234",
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_generic_error_with_status(self, mock_log_and_reject_error):
        """Test handling generic error with unknown content type."""
        mock_error = Mock()
        mock_error.headers = {
            'x-request-id': '1234',
            'content-type': 'application/xml'
        }
        mock_error.body = "<error>XML error</error>"
        mock_error.status = 503
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            SkyflowMessages.Error.GENERIC_API_ERROR.value,
            503,
            "1234",
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_no_content_type(self, mock_log_and_reject_error):
        """Test handling error without content-type header."""
        mock_error = Mock()
        mock_error.headers = {'x-request-id': '1234'}
        mock_error.body = "Some error"
        mock_error.status = 500
        mock_logger = Mock()

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            SkyflowMessages.Error.GENERIC_API_ERROR.value,
            500,
            "1234",
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_with_json_string(self, mock_log_and_reject_error):
        """Test handling JSON error when data is a JSON string."""
        error_json_string = json.dumps({
            "error": {
                "message": "String JSON error",
                "http_code": 422,
                "http_status": "Unprocessable Entity",
                "grpc_code": 3,
                "details": ["validation failed"]
            }
        })

        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id-3"

        handle_json_error(mock_error, error_json_string, request_id, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "String JSON error",
            422,
            request_id,
            "Unprocessable Entity",
            3,
            ["validation failed"],
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_with_invalid_json(self, mock_log_and_reject_error):
        """Test handling JSON decode error."""
        invalid_json = "This is not valid JSON"
        mock_error = Mock()
        mock_error.status = 500
        mock_logger = Mock()
        request_id = "test-request-id-4"

        handle_json_error(mock_error, invalid_json, request_id, mock_logger)

        # Should call with INVALID_JSON_RESPONSE error
        mock_log_and_reject_error.assert_called_once()
        self.assertEqual(
            mock_log_and_reject_error.call_args[0][0],
            SkyflowMessages.Error.INVALID_JSON_RESPONSE.value
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_missing_error_field(self, mock_log_and_reject_error):
        """Test handling JSON error with missing error field."""
        error_dict = {
            "message": "Error without error wrapper"
        }

        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id-5"

        handle_json_error(mock_error, error_dict, request_id, mock_logger)

        # Should use defaults for missing fields
        mock_log_and_reject_error.assert_called_once()
        args = mock_log_and_reject_error.call_args[0]
        # Default message when error field is missing
        self.assertEqual(args[0], SkyflowMessages.Error.UNKNOWN_ERROR_DEFAULT_MESSAGE.value)
        # Default status code
        self.assertEqual(args[1], 500)
        self.assertEqual(args[2], request_id)

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_text_error_with_status(self, mock_log_and_reject_error):
        """Test handle_text_error extracts status correctly."""
        mock_error = Mock()
        mock_error.status = 404
        mock_logger = Mock()
        request_id = "test-request-id-6"
        error_data = "Resource not found"

        from skyflow.utils._utils import handle_text_error
        handle_text_error(mock_error, error_data, request_id, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "Resource not found",
            404,
            request_id,
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_generic_error_with_status(self, mock_log_and_reject_error):
        """Test handle_generic_error_with_status."""
        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id-7"
        status = 503

        from skyflow.utils._utils import handle_generic_error_with_status
        handle_generic_error_with_status(mock_error, request_id, status, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            SkyflowMessages.Error.GENERIC_API_ERROR.value,
            503,
            request_id,
            logger=mock_logger
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_with_none_error(self, mock_log_and_reject_error):
        """Test handling None error object."""
        mock_logger = Mock()

        handle_exception(None, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            SkyflowMessages.Error.GENERIC_API_ERROR.value,
            SkyflowMessages.ErrorCodes.SERVER_ERROR.value,
            None,
            logger=mock_logger
        )

    #failed
    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_exception_with_empty_string_error(self, mock_log_and_reject_error):
        """Test handling empty string error."""
        mock_logger = Mock()
        mock_error = Mock()
        mock_error.headers = None
        mock_error.body = None

        handle_exception(mock_error, mock_logger)

        mock_log_and_reject_error.assert_called_once()
        # Should use str(error) or default message
        self.assertEqual(
            mock_log_and_reject_error.call_args[0][1],
            SkyflowMessages.ErrorCodes.SERVER_ERROR.value
        )

    @patch("skyflow.utils._utils.log_and_reject_error")
    def test_handle_json_error_with_bytes_data(self, mock_log_and_reject_error):
        """Test handling JSON error when data is bytes."""
        error_dict = {
            "error": {
                "message": "Bytes error",
                "http_code": 401,
                "http_status": "Unauthorized"
            }
        }
        error_bytes = json.dumps(error_dict).encode('utf-8')

        mock_error = Mock()
        mock_logger = Mock()
        request_id = "test-request-id-8"

        handle_json_error(mock_error, error_bytes, request_id, mock_logger)

        mock_log_and_reject_error.assert_called_once_with(
            "Bytes error",
            401,
            request_id,
            "Unauthorized",
            None,
            [],
            logger=mock_logger
        )

        # Add these new test methods to the TestUtils class:

    def test_construct_invoke_connection_request_with_no_headers(self):
        """Test construct_invoke_connection_request when headers are None."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param1": "value1"}
        mock_connection_request.headers = None
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {"query": "test"}

        connection_url = "https://example.com/{param1}/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)
        # Headers should be None when not provided
        self.assertIsNone(result.headers.get('Content-Type'))

    def test_construct_invoke_connection_request_with_xml_content_type(self):
        """Test construct_invoke_connection_request with XML content type."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": "application/xml"}
        mock_connection_request.body = {"root": {"child": "value"}}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)
        self.assertEqual(result.headers['content-type'], 'application/xml')
        # Body should be converted to XML
        self.assertIn('<root>', result.body)
        self.assertIn('<child>value</child>', result.body)

    def test_construct_invoke_connection_request_with_html_content_type(self):
        """Test construct_invoke_connection_request with HTML content type."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": "text/html"}
        mock_connection_request.body = {"message": "Hello"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)
        self.assertEqual(result.headers['content-type'], 'text/html')
        # Body should be JSON string for HTML
        self.assertEqual(result.body, json.dumps({"message": "Hello"}))

    def test_construct_invoke_connection_request_multipart_removes_content_type(self):
        """Test that Content-Type is removed for multipart/form-data."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.FORMDATA.value}
        mock_connection_request.body = {"field1": "value1", "field2": "value2"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)
        # Content-Type should be auto-generated by requests library
        self.assertIn('multipart/form-data', result.headers.get('Content-Type', ''))
        self.assertIn('boundary=', result.headers.get('Content-Type', ''))

    def test_construct_invoke_connection_request_with_no_body(self):
        """Test construct_invoke_connection_request when body is None."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        result = construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertIsInstance(result, PreparedRequest)
        self.assertIsNone(result.body)

    def test_get_data_from_content_type_url_encoded(self):
        """Test get_data_from_content_type with URL encoded content type."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"key1": "value1", "key2": "value2"}
        content_type = ContentType.URLENCODED.value

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, "key1=value1&key2=value2")
        self.assertEqual(files, {})

    def test_get_data_from_content_type_form_data(self):
        """Test get_data_from_content_type with form data content type."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"field1": "value1", "field2": "value2"}
        content_type = ContentType.FORMDATA.value

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertIsNone(converted_data)
        self.assertEqual(files["field1"], (None, "value1"))
        self.assertEqual(files["field2"], (None, "value2"))

    def test_get_data_from_content_type_json(self):
        """Test get_data_from_content_type with JSON content type."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"key": "value"}
        content_type = ContentType.JSON.value

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, json.dumps(data))
        self.assertEqual(files, {})

    def test_get_data_from_content_type_xml_with_dict(self):
        """Test get_data_from_content_type with XML content type and dict data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"root": {"child": "value"}}
        content_type = "application/xml"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertIn("<root>", converted_data)
        self.assertIn("<child>value</child>", converted_data)
        self.assertEqual(files, {})

    def test_get_data_from_content_type_xml_with_string(self):
        """Test get_data_from_content_type with XML content type and string data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = "<root><child>value</child></root>"
        content_type = "text/xml"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, data)
        self.assertEqual(files, {})

    def test_get_data_from_content_type_html_with_dict(self):
        """Test get_data_from_content_type with HTML content type and dict data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"message": "Hello"}
        content_type = "text/html"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, json.dumps(data))
        self.assertEqual(files, {})

    def test_get_data_from_content_type_html_with_string(self):
        """Test get_data_from_content_type with HTML content type and string data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = "<html><body>Hello</body></html>"
        content_type = "text/html"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, data)
        self.assertEqual(files, {})

    def test_get_data_from_content_type_unknown_type_with_dict(self):
        """Test get_data_from_content_type with unknown content type and dict data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = {"key": "value"}
        content_type = "application/custom"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, json.dumps(data))
        self.assertEqual(files, {})

    def test_get_data_from_content_type_unknown_type_with_string(self):
        """Test get_data_from_content_type with unknown content type and string data."""
        from skyflow.utils._utils import get_data_from_content_type

        data = "plain text data"
        content_type = "text/plain"

        converted_data, files = get_data_from_content_type(data, content_type)

        self.assertEqual(converted_data, data)
        self.assertEqual(files, {})

    def test_dict_to_xml_simple_dict(self):
        """Test dict_to_xml with simple dictionary."""
        from skyflow.utils._utils import dict_to_xml

        data = {"name": "John", "age": "30"}
        result = dict_to_xml(data)

        self.assertIn("<name>John</name>", result)
        self.assertIn("<age>30</age>", result)
        self.assertTrue(result.startswith("<root>"))
        self.assertTrue(result.endswith("</root>"))

    def test_dict_to_xml_nested_dict(self):
        """Test dict_to_xml with nested dictionary."""
        from skyflow.utils._utils import dict_to_xml

        data = {"person": {"name": "John", "age": "30"}}
        result = dict_to_xml(data)

        self.assertIn("<person>", result)
        self.assertIn("<name>John</name>", result)
        self.assertIn("<age>30</age>", result)

    def test_dict_to_xml_with_list(self):
        """Test dict_to_xml with list values."""
        from skyflow.utils._utils import dict_to_xml

        data = {"items": ["item1", "item2", "item3"]}
        result = dict_to_xml(data)

        self.assertIn("<items>item1</items>", result)
        self.assertIn("<items>item2</items>", result)
        self.assertIn("<items>item3</items>", result)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_xml_content(self, mock_response):
        """Test parsing XML response content."""
        mock_response.status_code = 200
        mock_response.content = b"<response><status>success</status></response>"
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "application/xml"
        }
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "<response><status>success</status></response>")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_url_encoded_content(self, mock_response):
        """Test parsing URL encoded response content."""
        mock_response.status_code = 200
        mock_response.content = b"card_number=4111111111111111&cvv=123"
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "application/x-www-form-urlencoded"
        }
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "card_number=4111111111111111&cvv=123")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_html_content(self, mock_response):
        """Test parsing HTML response content."""
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Success</body></html>"
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "text/html"
        }
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "<html><body>Success</body></html>")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_html_error(self, mock_response):
        """Test parsing HTML error response."""
        html_error = "<!DOCTYPE html><html><body><h1>Error 500</h1></body></html>"
        mock_response.status_code = 500
        mock_response.content = html_error.encode('utf-8')
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "text/html"
        }
        mock_response.raise_for_status = Mock(side_effect=HTTPError("500 Error"))

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        self.assertEqual(context.exception.message, html_error)
        self.assertEqual(context.exception.http_code, 500)
        self.assertEqual(context.exception.request_id, "1234")

    @patch("requests.Response")
    def test_parse_invoke_connection_response_json_decode_falls_back_to_string(self, mock_response):
        """Test that JSON decode error falls back to returning string content."""
        mock_response.status_code = 200
        mock_response.content = b"Not valid JSON but still success"
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "application/json"
        }
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "Not valid JSON but still success")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_no_content_type_with_json(self, mock_response):
        """Test parsing response with no content-type but valid JSON."""
        mock_response.status_code = 200
        mock_response.content = json.dumps({"success": True}).encode('utf-8')
        mock_response.headers = {"x-request-id": "1234"}
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, {"success": True})
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_no_content_type_with_text(self, mock_response):
        """Test parsing response with no content-type and non-JSON content."""
        mock_response.status_code = 200
        mock_response.content = b"Plain text response"
        mock_response.headers = {"x-request-id": "1234"}
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "Plain text response")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    @patch("requests.Response")
    def test_parse_invoke_connection_response_bytes_content(self, mock_response):
        """Test parsing response with bytes content."""
        mock_response.status_code = 200
        mock_response.content = b"Binary data response"
        mock_response.headers = {
            "x-request-id": "1234",
            "content-type": "application/octet-stream"
        }
        mock_response.raise_for_status = Mock()

        result = parse_invoke_connection_response(mock_response)

        self.assertIsInstance(result, InvokeConnectionResponse)
        self.assertEqual(result.data, "Binary data response")
        self.assertEqual(result.metadata["request_id"], "1234")
        self.assertIsNone(result.errors)

    def test_construct_invoke_connection_request_headers_json_error(self):
        """Test exception handling when json.dumps fails for headers."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}

        class UnserializableObject:
            def __repr__(self):
                raise TypeError("Object is not JSON serializable")

        mock_connection_request.headers = {"key": UnserializableObject()}
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with patch('json.dumps', side_effect=TypeError("Object is not JSON serializable")):
            with self.assertRaises(SkyflowError) as context:
                construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

            self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value)
            self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_headers_generic_exception(self):
        """Test generic exception handling for headers processing."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": "application/json"}
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with patch('skyflow.utils._utils.to_lowercase_keys', side_effect=Exception("Generic error")):
            with self.assertRaises(SkyflowError) as context:
                construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

            self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value)
            self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_body_processing_exception(self):
        """Test exception handling when body processing fails."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = {"key": "value"}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with patch('skyflow.utils._utils.get_data_from_content_type', side_effect=Exception("Body processing error")):
            with self.assertRaises(SkyflowError) as context:
                construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

            self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)
            self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_body_json_dumps_exception(self):
        """Test exception handling when json.dumps fails in get_data_from_content_type."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}

        class UnserializableObject:
            pass

        mock_connection_request.body = {"key": UnserializableObject()}
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with self.assertRaises(SkyflowError) as context:
            construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)
        self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_invalid_url_exception(self):
        """Test exception handling when requests.Request.prepare() fails with invalid URL."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = None
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with patch('requests.Request') as mock_request_class:
            mock_request_instance = Mock()
            mock_request_instance.prepare.side_effect = Exception("Invalid URL structure")
            mock_request_class.return_value = mock_request_instance

            with self.assertRaises(SkyflowError) as context:
                construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

            self.assertEqual(
                context.exception.message,
                SkyflowMessages.Error.INVALID_URL.value.format(connection_url)
            )
            self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_prepare_exception(self):
        """Test exception handling when prepare() method fails."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with patch('requests.Request') as mock_request_class:
            mock_request_instance = Mock()
            mock_request_instance.prepare.side_effect = Exception("Prepare failed")
            mock_request_class.return_value = mock_request_instance

            with self.assertRaises(SkyflowError) as context:
                construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

            self.assertEqual(
                context.exception.message,
                SkyflowMessages.Error.INVALID_URL.value.format(connection_url)
            )
            self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    def test_construct_invoke_connection_request_body_not_dict_raises_error(self):
        """Test that non-dict body raises SkyflowError which is caught and re-raised."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {}
        mock_connection_request.headers = {"Content-Type": ContentType.JSON.value}
        mock_connection_request.body = "not a dict"  # Invalid body type
        mock_connection_request.method.value = "POST"
        mock_connection_request.query_params = {}

        connection_url = "https://example.com/endpoint"

        with self.assertRaises(SkyflowError) as context:
            construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)
        self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

    @patch('skyflow.utils._utils.validate_invoke_connection_params')
    def test_construct_invoke_connection_request_validation_exception(self, mock_validate):
        """Test that validation exceptions are properly propagated."""
        mock_connection_request = Mock()
        mock_connection_request.path_params = {"param": "value"}
        mock_connection_request.headers = None
        mock_connection_request.body = None
        mock_connection_request.method.value = "GET"
        mock_connection_request.query_params = {"query": "value"}

        connection_url = "https://example.com/endpoint"

        mock_validate.side_effect = SkyflowError("Validation failed", 400)

        with self.assertRaises(SkyflowError) as context:
            construct_invoke_connection_request(mock_connection_request, connection_url, logger=None)

        self.assertEqual(context.exception.message, "Validation failed")
        self.assertEqual(context.exception.http_code, 400)
