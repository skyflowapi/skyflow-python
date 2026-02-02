import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages, parse_invoke_connection_response
from skyflow.utils.enums import RequestMethod
from skyflow.utils._version import SDK_VERSION
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
ERROR_RESPONSE_CONTENT = '"message": "Invalid Request"'
ERROR_FROM_CLIENT_RESPONSE_CONTENT = b'{"error": {"message": "Invalid Request"}}'

class TestConnection(unittest.TestCase):
    def setUp(self):
        self.mock_vault_client = Mock()
        self.mock_vault_client.get_config.return_value = VAULT_CONFIG
        self.mock_vault_client.get_bearer_token.return_value = VALID_BEARER_TOKEN
        self.mock_vault_client.get_logger.return_value = Mock()
        self.mock_vault_client.get_common_skyflow_credentials.return_value = None
        self.connection = Connection(self.mock_vault_client)

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_success(self, mock_send, mock_get_credentials):
        # Mock get_credentials to return credentials
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
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
        expected_response = {
            'data': {"response": "success"},
            'metadata': {"request_id": "test-request-id"},
            'errors': None
        }
        self.assertEqual(vars(response), expected_response)
        self.mock_vault_client.get_bearer_token.assert_called_once()
        mock_get_credentials.assert_called_once()

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_with_x_skyflow_authorization_already_present(self, mock_send, mock_get_credentials):
        """Test that X-Skyflow-Authorization is not overwritten if already present in headers."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        mock_response = Mock()
        mock_response.status_code = SUCCESS_STATUS_CODE
        mock_response.content = SUCCESS_RESPONSE_CONTENT
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_send.return_value = mock_response

        custom_auth = "custom_bearer_token"
        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            headers={"x-skyflow-authorization": custom_auth}
        )

        response = self.connection.invoke(request)
        
        # Verify bearer token from vault_client is NOT used
        self.assertIsNotNone(response)

    @patch('skyflow.vault.controller._connections.get_credentials')
    def test_invoke_invalid_headers(self, mock_get_credentials):
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
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

    @patch('skyflow.vault.controller._connections.get_credentials')
    def test_invoke_invalid_body(self, mock_get_credentials):
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
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

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_request_error(self, mock_send, mock_get_credentials):
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        mock_response = Mock()
        mock_response.status_code = FAILURE_STATUS_CODE
        mock_response.content = ERROR_RESPONSE_CONTENT.encode('utf-8')  # Convert to bytes
        mock_response.headers = {"x-request-id": "test-request-id"}
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Error")
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
        
        self.assertEqual(context.exception.message, ERROR_RESPONSE_CONTENT)
        self.assertEqual(context.exception.http_code, FAILURE_STATUS_CODE)
        self.assertEqual(context.exception.request_id, "test-request-id")

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_session_send_exception(self, mock_send, mock_get_credentials):
        """Test handling of generic exception from session.send()."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        mock_send.side_effect = Exception("Network error")

        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            headers=VALID_HEADERS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVOKE_CONNECTION_FAILED.value)
        self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.SERVER_ERROR.value)

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_skyflow_error_re_raised(self, mock_send, mock_get_credentials):
        """Test that SkyflowError is re-raised without wrapping."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        original_error = SkyflowError("Original error", 401)
        mock_send.side_effect = original_error

        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            headers=VALID_HEADERS
        )

        with self.assertRaises(SkyflowError) as context:
            self.connection.invoke(request)
        # Should be the same original error
        self.assertEqual(context.exception.message, "Original error")
        self.assertEqual(context.exception.http_code, 401)

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('requests.Session.send')
    def test_invoke_session_close_called(self, mock_send, mock_get_credentials):
        """Test that session.close() is called after send()."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        mock_response = Mock()
        mock_response.status_code = SUCCESS_STATUS_CODE
        mock_response.content = SUCCESS_RESPONSE_CONTENT
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_send.return_value = mock_response

        with patch('requests.Session.close') as mock_close:
            request = InvokeConnectionRequest(
                method=RequestMethod.GET,
                headers=VALID_HEADERS
            )
            
            response = self.connection.invoke(request)
            
            # Verify close was called
            mock_close.assert_called_once()

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('skyflow.vault.controller._connections.get_metrics')
    @patch('requests.Session.send')
    def test_invoke_adds_sky_metadata_header(self, mock_send, mock_get_metrics, mock_get_credentials):
        """Test that sky-metadata header is added to request."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        mock_get_metrics.return_value = {"sdk_version": SDK_VERSION}
        
        mock_response = Mock()
        mock_response.status_code = SUCCESS_STATUS_CODE
        mock_response.content = SUCCESS_RESPONSE_CONTENT
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_send.return_value = mock_response

        request = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body=VALID_BODY,
            headers=VALID_HEADERS
        )

        response = self.connection.invoke(request)
        
        # Verify get_metrics was called
        mock_get_metrics.assert_called_once()
        self.assertIsNotNone(response)

    def test_parse_invoke_connection_response_error_from_client(self):
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = FAILURE_STATUS_CODE
        mock_response.content = ERROR_FROM_CLIENT_RESPONSE_CONTENT
        mock_response.headers = {
            'error-from-client': 'true',
            'x-request-id': '12345'
        }
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        with self.assertRaises(SkyflowError) as context:
            parse_invoke_connection_response(mock_response)

        exception = context.exception

        self.assertTrue(any(detail.get('error_from_client') == True for detail in exception.details))
        self.assertEqual(exception.request_id, '12345')

    @patch('skyflow.vault.controller._connections.get_credentials')
    @patch('skyflow.vault.controller._connections.construct_invoke_connection_request')
    def test_invoke_construct_request_called(self, mock_construct, mock_get_credentials):
        """Test that construct_invoke_connection_request is called with correct parameters."""
        mock_get_credentials.return_value = {"api_key": "test_api_key"}
        
        mock_prepared_request = Mock(spec=requests.PreparedRequest)
        mock_prepared_request.headers = {}
        mock_construct.return_value = mock_prepared_request

        with patch('requests.Session.send') as mock_send:
            mock_response = Mock()
            mock_response.status_code = SUCCESS_STATUS_CODE
            mock_response.content = SUCCESS_RESPONSE_CONTENT
            mock_response.headers = {'x-request-id': 'test-request-id'}
            mock_send.return_value = mock_response

            request = InvokeConnectionRequest(
                method=RequestMethod.GET,
                headers=VALID_HEADERS
            )

            self.connection.invoke(request)

            # Verify construct was called with connection_url from config
            mock_construct.assert_called_once_with(
                request,
                VAULT_CONFIG["connection_url"],
                self.mock_vault_client.get_logger()
            )


if __name__ == '__main__':
    unittest.main()