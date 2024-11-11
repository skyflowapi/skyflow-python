import unittest
from unittest.mock import Mock, patch, call

from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.utils.enums import Method
from skyflow.vault.connection import InvokeConnectionRequest
from skyflow.vault.controller import Connection
from tests.constants.test_constants import VALID_BEARER_TOKEN, VAULT_CONFIG, SUCCESS_STATUS_CODE, \
    SUCCESS_RESPONSE_CONTENT, VALID_BODY, VALID_PATH_PARAMS, VALID_HEADERS, VALID_QUERY_PARAMS, INVALID_HEADERS, \
    INVALID_BODY, FAILURE_STATUS_CODE, ERROR_RESPONSE_CONTENT


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
            method=Method.POST,
            body=VALID_BODY,
            path_params=VALID_PATH_PARAMS,
            request_headers=VALID_HEADERS,
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
            request_headers=INVALID_HEADERS,
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
            request_headers=VALID_HEADERS,
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
            method=Method.POST,
            body=VALID_BODY,
            path_params=VALID_PATH_PARAMS,
            request_headers=VALID_HEADERS,
            query_params=VALID_QUERY_PARAMS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVOKE_CONNECTION_FAILED.value)


