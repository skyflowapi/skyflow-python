import unittest
import time
import jwt
import json
from unittest.mock import patch
import os
from skyflow.error import SkyflowError
from skyflow.service_account import is_expired, generate_bearer_token, \
    generate_bearer_token_from_creds
from skyflow.utils import SkyflowMessages
from skyflow.service_account._utils import get_service_account_token, get_signed_jwt, generate_signed_data_tokens, get_signed_data_token_response_object, generate_signed_data_tokens_from_creds

creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
with open(creds_path, 'r') as file:
    credentials = json.load(file)

VALID_CREDENTIALS_STRING = json.dumps(credentials)

CREDENTIALS_WITHOUT_CLIENT_ID = {
    'privateKey': 'private_key'
}

CREDENTIALS_WITHOUT_KEY_ID = {
    'privateKey': 'private_key',
    'clientID': 'client_id'
}

CREDENTIALS_WITHOUT_TOKEN_URI = {
    'privateKey': 'private_key',
    'clientID': 'client_id',
    'keyID': 'key_id'
}

VALID_SERVICE_ACCOUNT_CREDS = credentials

class TestServiceAccountUtils(unittest.TestCase):
    def test_is_expired_empty_token(self):
        self.assertTrue(is_expired(""))

    def test_is_expired_non_expired_token(self):
        future_time = time.time() + 1000
        token = jwt.encode({"exp": future_time}, key="test", algorithm="HS256")
        self.assertFalse(is_expired(token))

    def test_is_expired_expired_token(self):
        past_time = time.time() - 1000
        token =  jwt.encode({"exp": past_time}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))

    @patch("skyflow.utils.logger._log_helpers.log_error_log")
    @patch("jwt.decode", side_effect=Exception("Some error"))
    def test_is_expired_general_exception(self, mock_jwt_decode, mock_log_error):
        token = jwt.encode({"exp": time.time() + 1000}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_generate_bearer_token_invalid_file_path(self, mock_open):
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token("invalid_path")
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value)

    @patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "", 0))
    def test_generate_bearer_token_invalid_json(self, mock_json_load):
        creds_path = os.path.join(os.path.dirname(__file__), "invalid_creds.json")
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token(creds_path)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.FILE_INVALID_JSON.value.format(creds_path))

    @patch("skyflow.service_account._utils.get_service_account_token")
    def test_generate_bearer_token_valid_file_path(self, mock_generate_bearer_token):
        creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
        generate_bearer_token(creds_path)
        mock_generate_bearer_token.assert_called_once()

    @patch("skyflow.service_account._utils.get_service_account_token")
    def test_generate_bearer_token_from_creds_with_valid_json_string(self, mock_generate_bearer_token):
        generate_bearer_token_from_creds(VALID_CREDENTIALS_STRING)
        mock_generate_bearer_token.assert_called_once()

    def test_generate_bearer_token_from_creds_invalid_json(self):
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token_from_creds("invalid_json")
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value)

    def test_get_service_account_token_missing_private_key(self):
        incomplete_credentials = {}
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(incomplete_credentials, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_PRIVATE_KEY.value)

    def test_get_service_account_token_missing_client_id_key(self):
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(CREDENTIALS_WITHOUT_CLIENT_ID, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_CLIENT_ID.value)

    def test_get_service_account_token_missing_key_id_key(self):
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(CREDENTIALS_WITHOUT_KEY_ID, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_KEY_ID.value)

    def test_get_service_account_token_missing_token_uri_key(self):
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(CREDENTIALS_WITHOUT_TOKEN_URI, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_TOKEN_URI.value)

    def test_get_service_account_token_with_valid_credentials(self):
        access_token, _ = get_service_account_token(VALID_SERVICE_ACCOUNT_CREDS, {}, None)
        self.assertTrue(access_token)


    @patch("jwt.encode", side_effect=Exception)
    def test_get_signed_jwt_invalid_format(self, mock_jwt_encode):
        with self.assertRaises(SkyflowError) as context:
            get_signed_jwt({}, "client_id", "key_id", "token_uri", "private_key", None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.JWT_INVALID_FORMAT.value)

    def test_get_signed_data_token_response_object(self):
        token = "sample_token"
        signed_token = "signed_sample_token"
        response = get_signed_data_token_response_object(signed_token, token)
        self.assertEqual(response[0], token)
        self.assertEqual(response[1], signed_token)

    def test_generate_signed_data_tokens_from_file_path(self):
        creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
        options = {"data_tokens": ["token1", "token2"], "ctx": 'ctx'}
        result = generate_signed_data_tokens(creds_path, options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_invalid_file_path(self):
        options = {"data_tokens": ["token1", "token2"]}
        with self.assertRaises(SkyflowError) as context:
            result = generate_signed_data_tokens('credentials1.json', options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value)

    def test_generate_signed_data_tokens_from_creds(self):
        options = {"data_tokens": ["token1", "token2"]}
        result = generate_signed_data_tokens_from_creds(VALID_CREDENTIALS_STRING, options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_creds_with_invalid_string(self):
        options = {"data_tokens": ["token1", "token2"]}
        credentials_string = '{'
        with self.assertRaises(SkyflowError) as context:
            result = generate_signed_data_tokens_from_creds(credentials_string, options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value)

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_with_role_ids_formats_scope(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com"
        }
        options = {"role_ids": ["role1", "role2"]}
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        mock_auth_api.authentication_service_get_auth_token.return_value = type("obj", (), {"access_token": "token",
                                                                                            "token_type": "bearer"})
        access_token, token_type = get_service_account_token(creds, options, None)
        self.assertEqual(access_token, "token")
        self.assertEqual(token_type, "bearer")
        args, kwargs = mock_auth_api.authentication_service_get_auth_token.call_args
        self.assertIn("scope", kwargs)
        self.assertEqual(kwargs["scope"], "role:role1 role:role2")

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_unauthorized_error(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com"
        }
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        from skyflow.generated.rest.errors.unauthorized_error import UnauthorizedError
        mock_auth_api.authentication_service_get_auth_token.side_effect = UnauthorizedError("unauthorized")
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(context.exception.message,
                         SkyflowMessages.Error.UNAUTHORIZED_ERROR_IN_GETTING_BEARER_TOKEN.value)

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_generic_exception(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com"
        }
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        mock_auth_api.authentication_service_get_auth_token.side_effect = Exception("some error")
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.FAILED_TO_GET_BEARER_TOKEN.value)

    @patch("jwt.encode", side_effect=Exception("jwt error"))
    def test_get_signed_tokens_jwt_encode_exception(self, mock_jwt_encode):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com"
        }
        options = {"data_tokens": ["token1"]}
        with self.assertRaises(SkyflowError) as context:
            from skyflow.service_account._utils import get_signed_tokens
            get_signed_tokens(creds, options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS.value)