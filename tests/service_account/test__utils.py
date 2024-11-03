import unittest
import time
import jwt
import json
from unittest.mock import patch

from skyflow.error import SkyflowError
from skyflow.service_account import is_expired, generate_bearer_token, \
    generate_bearer_token_from_creds
from skyflow.utils import SkyflowMessages
from skyflow.service_account._utils import get_service_account_token, get_signed_jwt, generate_signed_data_tokens, get_signed_data_token_response_object, generate_signed_data_tokens_from_creds
from tests.constants.test_constants import VALID_CREDENTIALS_STRING, CREDENTIALS_WITHOUT_CLIENT_ID, \
    CREDENTIALS_WITHOUT_KEY_ID, CREDENTIALS_WITHOUT_TOKEN_URI, VALID_SERVICE_ACCOUNT_CREDS


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

    @patch("skyflow.service_account._utils.log_error")
    @patch("jwt.decode", side_effect=Exception("Some error"))
    def test_is_expired_general_exception(self, mock_jwt_decode, mock_log_error):
        token = jwt.encode({"exp": time.time() + 1000}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))
        mock_log_error.assert_called_once_with(
            SkyflowMessages.Error.JWT_DECODE_ERROR.value, 400, logger=None
        )

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_generate_bearer_token_invalid_file_path(self, mock_open):
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token("invalid_path")
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value)

    @patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "", 0))
    def test_generate_bearer_token_invalid_json(self, mock_json_load):
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token("credentials.json")
        self.assertEqual(context.exception.message, SkyflowMessages.Error.FILE_INVALID_JSON.value.format("credentials.json"))

    @patch("skyflow.service_account._utils.get_service_account_token")
    def test_generate_bearer_token_valid_file_path(self, mock_generate_bearer_token):
        generate_bearer_token("credentials.json")
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
        self.assertEqual(response["token"], token)
        self.assertEqual(response["signed_token"], signed_token)

    def test_generate_signed_data_tokens_from_file_path(self):
        options = {"data_tokens": ["token1", "token2"], "ctx": 'ctx'}
        result = generate_signed_data_tokens('credentials.json', options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_invalid_file_path(self):
        options = {"data_tokens": ["token1", "token2"]}
        with self.assertRaises(SkyflowError) as context:
            result = generate_signed_data_tokens('credentials1.json', options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value)

    # def test_generate_signed_data_tokens_from_valid_file_path_with_invalid_credentials(self):
    #     options = {"data_tokens": ["token1", "token2"]}
    #     with self.assertRaises(SkyflowError) as context:
    #         result = generate_signed_data_tokens("invalid_creds.json", options)
    #     self.assertEqual(context.exception.message, SkyflowMessages.Error.FILE_INVALID_JSON.value.format("invalid_creds.json"))

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