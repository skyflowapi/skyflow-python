import unittest
from unittest.mock import Mock, patch

from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.utils.enums import RequestMethod
from skyflow.vault.connection import InvokeConnectionRequest
from skyflow.vault.controller import Connection

VALID_BEARER_TOKEN = "test_bearer_token"
VAULT_CONFIG = {
    "credentials": {"api_key": "test_api_key"},
    "connection_url": "https://CONNECTION_URL"
}
SUCCESS_STATUS_CODE = 200
SUCCESS_RESPONSE_CONTENT = '{"response": "success"}'
VALID_BODY = {"key": "value"}
VALID_PATH_PARAMS = {"path_key": "value"}
VALID_HEADERS = {"Content-Type": "application/json"}
VALID_QUERY_PARAMS = {"query_key": "value"}
INVALID_HEADERS = "invalid_headers"
INVALID_BODY = "invalid_body"
FAILURE_STATUS_CODE = 400
ERROR_RESPONSE_CONTENT = '{"error": {"message": "error occurred"}}'

class TestConnection(unittest.TestCase):
    def setUp(self):
        self.mock_vault_client = Mock()
        self.mock_vault_client.get_config.return_value = VAULT_CONFIG
        self.mock_vault_client.get_bearer_token.return_value = VALID_BEARER_TOKEN
        self.connection = Connection(self.mock_vault_client)

    @patch('requests.Session.send')
    def test_invoke_success(self, mock_send):
        # Mocking successful response
        mock_response = Mock()
        mock_response.status_code = SUCCESS_STATUS_CODE
        mock_response.content = SUCCESS_RESPONSE_CONTENT
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_send.return_value = mock_response

        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            path_params=VALID_PATH_PARAMS,
            headers=VALID_HEADERS,
            query_params=VALID_QUERY_PARAMS
        )

        # Test invoke method
        response = self.connection.invoke(request)

        # Assertions for successful invocation
        self.assertEqual(response.response, {"response": "success", "request_id": "test-request-id"})
        self.mock_vault_client.get_bearer_token.assert_called_once()

    @patch('requests.Session.send')
    def test_invoke_invalid_headers(self, mock_send):
        request = InvokeConnectionRequest(
            method="POST",
            body=VALID_BODY,
            path_params=VALID_PATH_PARAMS,
            headers=INVALID_HEADERS,
            query_params=VALID_QUERY_PARAMS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value)

    @patch('requests.Session.send')
    def test_invoke_invalid_body(self, mock_send):
        request = InvokeConnectionRequest(
            method="POST",
            body=INVALID_BODY,
            path_params=VALID_PATH_PARAMS,
            headers=VALID_HEADERS,
            query_params=VALID_QUERY_PARAMS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)

    @patch('requests.Session.send')
    def test_invoke_request_error(self, mock_send):
        mock_response = Mock()
        mock_response.status_code = FAILURE_STATUS_CODE
        mock_response.content = ERROR_RESPONSE_CONTENT
        mock_send.return_value = mock_response

        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            path_params=VALID_PATH_PARAMS,
            headers=VALID_HEADERS,
            query_params=VALID_QUERY_PARAMS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVOKE_CONNECTION_FAILED.value)


