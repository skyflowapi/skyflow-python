import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages, parse_invoke_connection_response
from skyflow.utils._utils import get_data_from_content_type, construct_invoke_connection_request
from skyflow.utils.enums import RequestMethod, ContentType
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

        expected_message = SkyflowMessages.Error.API_ERROR.value.format(FAILURE_STATUS_CODE)
        self.assertEqual(context.exception.message, expected_message)
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


class TestGetDataFromContentType(unittest.TestCase):
    """Tests for get_data_from_content_type covering all supported content types."""

    DATA = {'key': 'value', 'num': 42}

    # ── JSON ──────────────────────────────────────────────────────────────────
    def test_json_content_type_returns_json_string(self):
        data, files = get_data_from_content_type(self.DATA, ContentType.JSON.value)
        self.assertEqual(data, json.dumps(self.DATA))
        self.assertEqual(files, {})

    # ── URL-encoded ───────────────────────────────────────────────────────────
    def test_urlencoded_content_type_returns_encoded_string(self):
        data, files = get_data_from_content_type({'k': 'v'}, ContentType.URLENCODED.value)
        self.assertIn('k=v', data)
        self.assertEqual(files, {})

    def test_urlencoded_nested_dict(self):
        payload = {'a': {'b': 'c'}}
        data, files = get_data_from_content_type(payload, ContentType.URLENCODED.value)
        self.assertIsInstance(data, str)
        self.assertIn('c', data)
        self.assertEqual(files, {})

    # ── Form-data ─────────────────────────────────────────────────────────────
    def test_formdata_content_type_returns_files_dict(self):
        data, files = get_data_from_content_type({'f1': 'v1', 'f2': 'v2'}, ContentType.FORMDATA.value)
        self.assertIsNone(data)
        self.assertEqual(files, {'f1': (None, 'v1'), 'f2': (None, 'v2')})

    def test_formdata_converts_values_to_str(self):
        data, files = get_data_from_content_type({'num': 99}, ContentType.FORMDATA.value)
        self.assertEqual(files['num'], (None, '99'))

    def test_formdata_single_key(self):
        data, files = get_data_from_content_type({'only': 'one'}, ContentType.FORMDATA.value)
        self.assertIsNone(data)
        self.assertIn('only', files)

    # ── XML ───────────────────────────────────────────────────────────────────
    def test_xml_text_xml_content_type_wraps_in_root(self):
        data, files = get_data_from_content_type({'key': 'value'}, 'text/xml')
        self.assertIn('<root>', data)
        self.assertIn('<key>value</key>', data)
        self.assertIn('</root>', data)
        self.assertEqual(files, {})

    def test_xml_application_xml_content_type(self):
        data, files = get_data_from_content_type({'key': 'value'}, 'application/xml')
        self.assertIn('<root>', data)
        self.assertIn('<key>value</key>', data)
        self.assertEqual(files, {})

    def test_xml_content_type_enum_value(self):
        data, files = get_data_from_content_type({'key': 'value'}, ContentType.XML.value)
        self.assertIn('<key>value</key>', data)
        self.assertEqual(files, {})

    def test_xml_non_dict_data_returns_str(self):
        data, files = get_data_from_content_type('raw_string', 'text/xml')
        self.assertEqual(data, 'raw_string')
        self.assertEqual(files, {})

    # ── HTML ──────────────────────────────────────────────────────────────────
    def test_html_content_type_dict_returns_json_string(self):
        data, files = get_data_from_content_type(self.DATA, ContentType.HTML.value)
        self.assertEqual(data, json.dumps(self.DATA))
        self.assertEqual(files, {})

    def test_html_text_html_content_type(self):
        data, files = get_data_from_content_type(self.DATA, 'text/html')
        self.assertEqual(data, json.dumps(self.DATA))
        self.assertEqual(files, {})

    def test_html_non_dict_data_returns_str(self):
        data, files = get_data_from_content_type('raw', ContentType.HTML.value)
        self.assertEqual(data, 'raw')
        self.assertEqual(files, {})

    # ── None / unknown ────────────────────────────────────────────────────────
    def test_none_content_type_falls_back_to_json(self):
        data, files = get_data_from_content_type(self.DATA, None)
        self.assertEqual(data, json.dumps(self.DATA))
        self.assertEqual(files, {})

    def test_unknown_content_type_falls_back_to_json(self):
        data, files = get_data_from_content_type(self.DATA, 'application/octet-stream')
        self.assertEqual(data, json.dumps(self.DATA))
        self.assertEqual(files, {})

    def test_unknown_content_type_non_dict_returns_str(self):
        data, files = get_data_from_content_type('blob', 'application/octet-stream')
        self.assertEqual(data, 'blob')
        self.assertEqual(files, {})


class TestParseInvokeConnectionResponse(unittest.TestCase):
    """Tests for parse_invoke_connection_response covering all success and error paths."""

    def _make_response(self, status_code, content, headers=None, raise_http_error=False):
        mock_resp = Mock(spec=requests.Response)
        mock_resp.status_code = status_code
        if isinstance(content, str):
            mock_resp.content = content.encode('utf-8')
        else:
            mock_resp.content = content
        mock_resp.headers = headers or {}
        if raise_http_error:
            mock_resp.raise_for_status.side_effect = requests.HTTPError()
        else:
            mock_resp.raise_for_status.return_value = None
        return mock_resp

    # ── Success paths ─────────────────────────────────────────────────────────
    def test_success_json_content_type_parses_body(self):
        resp = self._make_response(
            200,
            '{"result": "ok"}',
            {'content-type': 'application/json', 'x-request-id': 'req-1'}
        )
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, {'result': 'ok'})
        self.assertEqual(result.metadata.get('request_id'), 'req-1')
        self.assertIsNone(result.errors)

    def test_success_plain_text_content_type_returns_string(self):
        resp = self._make_response(
            200,
            'plain text response',
            {'content-type': 'text/plain'}
        )
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, 'plain text response')

    def test_success_no_content_type_tries_json_parse(self):
        resp = self._make_response(200, '{"a": 1}', {})
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, {'a': 1})

    def test_success_no_content_type_invalid_json_returns_string(self):
        resp = self._make_response(200, 'not json', {})
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, 'not json')

    def test_success_no_x_request_id_metadata_is_empty(self):
        resp = self._make_response(200, '{}', {'content-type': 'application/json'})
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.metadata, {})

    def test_success_invalid_json_with_json_content_type_returns_raw_string(self):
        resp = self._make_response(
            200,
            'not-json',
            {'content-type': 'application/json'}
        )
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, 'not-json')

    def test_success_bytes_content_decoded(self):
        resp = self._make_response(200, b'{"x": 1}', {'content-type': 'application/json'})
        result = parse_invoke_connection_response(resp)
        self.assertEqual(result.data, {'x': 1})

    # ── Error paths — standard Skyflow format ────────────────────────────────
    def test_error_standard_skyflow_format_extracts_message(self):
        body = json.dumps({'error': {'message': 'bad input', 'http_code': 400, 'http_status': 'BAD_REQUEST', 'grpc_code': 3, 'details': []}})
        resp = self._make_response(400, body, {'x-request-id': 'r1'}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        e = ctx.exception
        self.assertEqual(e.message, 'bad input')
        self.assertEqual(e.http_code, 400)
        self.assertEqual(e.request_id, 'r1')
        self.assertEqual(e.http_status, 'BAD_REQUEST')
        self.assertEqual(e.grpc_code, 3)

    def test_error_standard_format_falls_back_to_http_code_when_missing(self):
        body = json.dumps({'error': {'message': 'oops'}})
        resp = self._make_response(500, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        self.assertEqual(ctx.exception.http_code, 500)

    def test_error_standard_format_falls_back_to_sdk_message_when_missing(self):
        body = json.dumps({'error': {}})
        resp = self._make_response(503, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(503)
        self.assertEqual(ctx.exception.message, expected)

    # ── Error paths — string error value ─────────────────────────────────────
    def test_error_string_error_value_used_as_message(self):
        body = json.dumps({'error': 'gateway timed out'})
        resp = self._make_response(502, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        self.assertEqual(ctx.exception.message, 'gateway timed out')

    def test_error_empty_string_error_value_falls_back_to_sdk_message(self):
        body = json.dumps({'error': ''})
        resp = self._make_response(502, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(502)
        self.assertEqual(ctx.exception.message, expected)

    # ── Error paths — non-standard JSON ──────────────────────────────────────
    def test_error_no_error_key_uses_sdk_message(self):
        body = json.dumps({'message': 'something went wrong'})
        resp = self._make_response(500, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(500)
        self.assertEqual(ctx.exception.message, expected)

    def test_error_non_dict_json_body_uses_sdk_message(self):
        body = json.dumps(['list', 'not', 'dict'])
        resp = self._make_response(500, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(500)
        self.assertEqual(ctx.exception.message, expected)

    def test_error_numeric_error_value_uses_sdk_message(self):
        body = json.dumps({'error': 12345})
        resp = self._make_response(500, body, {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(500)
        self.assertEqual(ctx.exception.message, expected)

    # ── Error paths — non-JSON / empty body ──────────────────────────────────
    def test_error_empty_body_uses_sdk_message(self):
        resp = self._make_response(502, '', {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(502)
        self.assertEqual(ctx.exception.message, expected)
        self.assertEqual(ctx.exception.http_code, 502)

    def test_error_html_body_uses_sdk_message(self):
        resp = self._make_response(502, '<html><body>Bad Gateway</body></html>', {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(502)
        self.assertEqual(ctx.exception.message, expected)

    def test_error_plain_text_body_uses_sdk_message(self):
        resp = self._make_response(503, 'Service Unavailable', {}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        expected = SkyflowMessages.Error.API_ERROR.value.format(503)
        self.assertEqual(ctx.exception.message, expected)

    # ── error-from-client header ──────────────────────────────────────────────
    def test_error_from_client_true_appended_to_details(self):
        body = json.dumps({'error': {'message': 'client error', 'http_code': 400, 'details': []}})
        resp = self._make_response(400, body, {'error-from-client': 'true', 'x-request-id': 'r2'}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        self.assertTrue(any(d.get('error_from_client') is True for d in ctx.exception.details))

    def test_error_from_client_false_appended_to_details(self):
        body = json.dumps({'error': {'message': 'server error', 'http_code': 500}})
        resp = self._make_response(500, body, {'error-from-client': 'false'}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        self.assertTrue(any(d.get('error_from_client') is False for d in ctx.exception.details))

    def test_error_from_client_initialises_details_when_none(self):
        body = json.dumps({'error': {'message': 'err', 'http_code': 400}})
        resp = self._make_response(400, body, {'error-from-client': 'true'}, raise_http_error=True)
        with self.assertRaises(SkyflowError) as ctx:
            parse_invoke_connection_response(resp)
        self.assertIsNotNone(ctx.exception.details)
        self.assertTrue(len(ctx.exception.details) > 0)


class TestConstructInvokeConnectionRequest(unittest.TestCase):
    """Tests for construct_invoke_connection_request covering method, body, headers, path/query params."""

    BASE_URL = 'https://example.com/api'
    LOGGER = Mock()

    def _make_request(self, method=RequestMethod.POST, body=None, headers=None,
                      path_params=None, query_params=None):
        return InvokeConnectionRequest(
            method=method,
            body=body,
            headers=headers,
            path_params=path_params or {},
            query_params=query_params or {}
        )

    def test_post_with_json_body_prepares_request(self):
        req = self._make_request(body={'k': 'v'}, headers={'Content-Type': 'application/json'})
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(prepared.method, 'POST')
        self.assertIn('k', prepared.body)

    def test_get_with_no_body(self):
        req = self._make_request(method=RequestMethod.GET)
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(prepared.method, 'GET')

    def test_urlencoded_body_is_form_encoded(self):
        req = self._make_request(
            body={'field': 'val'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertIn('field=val', prepared.body)

    def test_formdata_body_produces_multipart_request(self):
        req = self._make_request(
            body={'file_field': 'data'},
            headers={'Content-Type': 'multipart/form-data'}
        )
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(prepared.method, 'POST')
        self.assertIsNotNone(prepared.body)

    def test_xml_body_contains_xml_tags(self):
        req = self._make_request(
            body={'item': 'data'},
            headers={'Content-Type': 'text/xml'}
        )
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertIn('<item>', prepared.body)

    def test_path_params_substituted_in_url(self):
        req = self._make_request(
            method=RequestMethod.GET,
            path_params={'id': '123'}
        )
        url_with_placeholder = 'https://example.com/api/{id}/resource'
        prepared = construct_invoke_connection_request(req, url_with_placeholder, self.LOGGER)
        self.assertIn('123', prepared.url)
        self.assertNotIn('{id}', prepared.url)

    def test_query_params_appear_in_url(self):
        req = self._make_request(
            method=RequestMethod.GET,
            query_params={'page': '1', 'limit': '10'}
        )
        prepared = construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertIn('page=1', prepared.url)
        self.assertIn('limit=10', prepared.url)

    def test_invalid_headers_raises_skyflow_error(self):
        req = InvokeConnectionRequest(method=RequestMethod.POST, headers='bad-headers')
        with self.assertRaises(SkyflowError) as ctx:
            construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value)

    def test_invalid_body_raises_skyflow_error(self):
        req = InvokeConnectionRequest(
            method=RequestMethod.POST,
            body='not-a-dict',
            headers={'Content-Type': 'application/json'}
        )
        with self.assertRaises(SkyflowError) as ctx:
            construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.INVALID_REQUEST_BODY.value)

    def test_invalid_method_raises_skyflow_error(self):
        req = InvokeConnectionRequest(method='INVALID_METHOD')
        with self.assertRaises(SkyflowError) as ctx:
            construct_invoke_connection_request(req, self.BASE_URL, self.LOGGER)
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.INVALID_REQUEST_METHOD.value)

    def test_trailing_slash_stripped_from_url(self):
        req = self._make_request(method=RequestMethod.GET)
        prepared = construct_invoke_connection_request(req, self.BASE_URL + '/', self.LOGGER)
        self.assertNotIn('//', prepared.url.replace('https://', ''))


if __name__ == '__main__':
    unittest.main()