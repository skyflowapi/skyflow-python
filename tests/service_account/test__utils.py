import unittest
import time
import jwt
import json
from unittest.mock import patch
import os
from skyflow.error import SkyflowError
from skyflow.service_account import is_expired, generate_bearer_token, generate_bearer_token_from_creds
from skyflow.utils import SkyflowMessages
from skyflow.service_account._utils import (
    get_service_account_token,
    get_signed_jwt,
    generate_signed_data_tokens,
    get_signed_data_token_response_object,
    generate_signed_data_tokens_from_creds,
    _validate_and_resolve_ctx,
    _normalize_credentials,
    get_signed_tokens,
)

creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")
with open(creds_path, "r") as file:
    credentials = json.load(file)

VALID_CREDENTIALS_STRING = json.dumps(credentials)

CREDENTIALS_WITHOUT_CLIENT_ID = {"privateKey": "private_key"}

CREDENTIALS_WITHOUT_KEY_ID = {"privateKey": "private_key", "clientID": "client_id"}

CREDENTIALS_WITHOUT_TOKEN_URI = {"privateKey": "private_key", "clientID": "client_id", "keyID": "key_id"}

VALID_SERVICE_ACCOUNT_CREDS = credentials

# Snake-case version of the real credentials (keys remapped to snake_case)
SNAKE_CASE_CREDS = {
    "private_key": credentials["privateKey"],
    "client_id": credentials["clientID"],
    "key_id": credentials["keyID"],
    "token_uri": credentials["tokenURI"],
}

SNAKE_CASE_CREDS_STRING = json.dumps(
    {
        "private_key": credentials["privateKey"],
        "client_id": credentials["clientID"],
        "key_id": credentials["keyID"],
        "token_uri": credentials["tokenURI"],
    }
)


class TestServiceAccountUtils(unittest.TestCase):
    # ── is_expired ────────────────────────────────────────────────────────────

    def test_is_expired_none_token(self):
        self.assertTrue(is_expired(None))

    def test_is_expired_empty_token(self):
        self.assertTrue(is_expired(""))

    def test_is_expired_non_expired_token(self):
        future_time = time.time() + 1000
        token = jwt.encode({"exp": future_time}, key="test", algorithm="HS256")
        self.assertFalse(is_expired(token))

    def test_is_expired_expired_token(self):
        past_time = time.time() - 1000
        token = jwt.encode({"exp": past_time}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))

    @patch("skyflow.utils.logger._log_helpers.log_error_log")
    @patch("jwt.decode", side_effect=Exception("Some error"))
    def test_is_expired_general_exception(self, mock_jwt_decode, mock_log_error):
        token = jwt.encode({"exp": time.time() + 1000}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))

    # ── generate_bearer_token ─────────────────────────────────────────────────

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

    # ── generate_bearer_token_from_creds ──────────────────────────────────────

    @patch("skyflow.service_account._utils.get_service_account_token")
    def test_generate_bearer_token_from_creds_with_valid_json_string(self, mock_generate_bearer_token):
        generate_bearer_token_from_creds(VALID_CREDENTIALS_STRING)
        mock_generate_bearer_token.assert_called_once()

    def test_generate_bearer_token_from_creds_invalid_json(self):
        with self.assertRaises(SkyflowError) as context:
            generate_bearer_token_from_creds("invalid_json")
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value)

    # ── get_service_account_token ─────────────────────────────────────────────

    def test_get_service_account_token_missing_private_key(self):
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token({}, {}, None)
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

    def test_get_service_account_token_with_snake_case_creds(self):
        access_token, _ = get_service_account_token(SNAKE_CASE_CREDS, {}, None)
        self.assertTrue(access_token)

    def test_get_service_account_token_missing_private_key_snake(self):
        creds = {
            "client_id": "id",
            "key_id": "kid",
            "token_uri": "https://example.com",
        }
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_PRIVATE_KEY.value)

    def test_get_service_account_token_invalid_token_uri(self):
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "not-a-url",
        }
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_get_service_account_token_invalid_token_uri_in_options(self):
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "https://valid-url.com",
        }
        options = {"token_uri": "not-a-valid-url"}
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, options, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_with_role_ids_formats_scope(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com",
        }
        options = {"role_ids": ["role1", "role2"]}
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        mock_auth_api.authentication_service_get_auth_token.return_value = type(
            "obj", (), {"access_token": "token", "token_type": "bearer"}
        )
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
            "tokenURI": "https://valid-url.com",
        }
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        from skyflow.generated.rest.errors.unauthorized_error import UnauthorizedError

        mock_auth_api.authentication_service_get_auth_token.side_effect = UnauthorizedError("unauthorized")
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(
            context.exception.message, SkyflowMessages.Error.UNAUTHORIZED_ERROR_IN_GETTING_BEARER_TOKEN.value
        )

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_generic_exception(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com",
        }
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        mock_auth_api.authentication_service_get_auth_token.side_effect = Exception("some error")
        with self.assertRaises(SkyflowError) as context:
            get_service_account_token(creds, {}, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.FAILED_TO_GET_BEARER_TOKEN.value)

    # ── get_signed_jwt ────────────────────────────────────────────────────────

    @patch("jwt.encode", side_effect=Exception)
    def test_get_signed_jwt_invalid_format(self, mock_jwt_encode):
        with self.assertRaises(SkyflowError) as context:
            get_signed_jwt({}, "client_id", "key_id", "token_uri", "private_key", None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.JWT_INVALID_FORMAT.value)

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_jwt_with_valid_string_ctx(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "mock_token"
        get_signed_jwt({"ctx": "valid_ctx"}, "client_id", "key_id", "token_uri", "private_key", None)
        payload = mock_jwt_encode.call_args.kwargs["payload"]
        self.assertEqual(payload["ctx"], "valid_ctx")

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_jwt_with_valid_dict_ctx(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "mock_token"
        get_signed_jwt({"ctx": {"role": "admin"}}, "client_id", "key_id", "token_uri", "private_key", None)
        payload = mock_jwt_encode.call_args.kwargs["payload"]
        self.assertEqual(payload["ctx"], {"role": "admin"})

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_jwt_with_empty_string_ctx_not_added(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "mock_token"
        get_signed_jwt({"ctx": ""}, "client_id", "key_id", "token_uri", "private_key", None)
        payload = mock_jwt_encode.call_args.kwargs["payload"]
        self.assertNotIn("ctx", payload)

    # ── get_signed_data_token_response_object ─────────────────────────────────

    def test_get_signed_data_token_response_object(self):
        token = "sample_token"
        signed_token = "signed_sample_token"
        response = get_signed_data_token_response_object(signed_token, token)
        self.assertIsInstance(response, tuple)
        self.assertEqual(response[0], token)
        self.assertEqual(response[1], signed_token)

    # ── get_signed_tokens ─────────────────────────────────────────────────────

    @patch("jwt.encode", side_effect=Exception("jwt error"))
    def test_get_signed_tokens_jwt_encode_exception(self, mock_jwt_encode):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com",
        }
        options = {"data_tokens": ["token1"]}
        with self.assertRaises(SkyflowError) as context:
            get_signed_tokens(creds, options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS.value)

    def test_get_signed_tokens_returns_list_one_per_token(self):
        result = generate_signed_data_tokens(creds_path, {"data_tokens": ["token1", "token2"]})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_get_signed_tokens_items_are_tuples_with_token_and_signed_token(self):
        result = generate_signed_data_tokens(creds_path, {"data_tokens": ["token1", "token2"]})
        for item in result:
            self.assertIsInstance(item, tuple)
        self.assertEqual(result[0][0], "token1")
        self.assertEqual(result[1][0], "token2")
        self.assertTrue(result[0][1].startswith("signed_token_"))
        self.assertTrue(result[1][1].startswith("signed_token_"))

    def test_get_signed_tokens_returns_list_single_token(self):
        result = generate_signed_data_tokens(creds_path, {"data_tokens": ["token1"]})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_get_signed_tokens_empty_data_tokens_returns_empty_list(self):
        result = generate_signed_data_tokens(creds_path, {"data_tokens": []})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_tokens_with_string_ctx_in_claims(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "signed"
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "https://valid-url.com",
        }
        get_signed_tokens(creds, {"data_tokens": ["tok1"], "ctx": "my_ctx"})
        call_args = mock_jwt_encode.call_args
        claims = call_args[0][0] if call_args[0] else call_args.kwargs.get("args", [None])[0]
        # jwt.encode(claims, key, algorithm=...) — first positional arg is claims
        claims_arg = mock_jwt_encode.call_args[0][0]
        self.assertEqual(claims_arg["ctx"], "my_ctx")

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_tokens_with_dict_ctx_in_claims(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "signed"
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "https://valid-url.com",
        }
        ctx_dict = {"role": "admin", "dept": "eng"}
        get_signed_tokens(creds, {"data_tokens": ["tok1"], "ctx": ctx_dict})
        claims_arg = mock_jwt_encode.call_args[0][0]
        self.assertEqual(claims_arg["ctx"], ctx_dict)

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_tokens_with_empty_ctx_not_in_claims(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "signed"
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "https://valid-url.com",
        }
        get_signed_tokens(creds, {"data_tokens": ["tok1"], "ctx": ""})
        claims_arg = mock_jwt_encode.call_args[0][0]
        self.assertNotIn("ctx", claims_arg)

    @patch("skyflow.service_account._utils.jwt.encode")
    def test_get_signed_tokens_with_none_ctx_not_in_claims(self, mock_jwt_encode):
        mock_jwt_encode.return_value = "signed"
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "https://valid-url.com",
        }
        get_signed_tokens(creds, {"data_tokens": ["tok1"], "ctx": None})
        claims_arg = mock_jwt_encode.call_args[0][0]
        self.assertNotIn("ctx", claims_arg)

    def test_get_signed_tokens_invalid_token_uri(self):
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
            "tokenURI": "not-a-url",
        }
        with self.assertRaises(SkyflowError) as context:
            get_signed_tokens(creds, {"data_tokens": ["tok1"]})
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_get_signed_tokens_missing_token_uri(self):
        creds = {
            "privateKey": "key",
            "clientID": "id",
            "keyID": "kid",
        }
        with self.assertRaises(SkyflowError) as context:
            get_signed_tokens(creds, {"data_tokens": ["tok1"]})
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_get_signed_tokens_with_snake_case_creds(self):
        result = get_signed_tokens(SNAKE_CASE_CREDS, {"data_tokens": ["token1", "token2"]})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    # ── generate_signed_data_tokens (file path) ───────────────────────────────

    def test_generate_signed_data_tokens_from_file_path(self):
        options = {"data_tokens": ["token1", "token2"], "ctx": "ctx"}
        result = generate_signed_data_tokens(creds_path, options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_invalid_file_path(self):
        options = {"data_tokens": ["token1", "token2"]}
        with self.assertRaises(SkyflowError) as context:
            generate_signed_data_tokens("credentials1.json", options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value)

    def test_generate_signed_data_tokens_with_dict_ctx(self):
        options = {"data_tokens": ["token1"], "ctx": {"role": "admin", "department": "finance"}}
        result = generate_signed_data_tokens(creds_path, options)
        self.assertEqual(len(result), 1)

    # ── generate_signed_data_tokens_from_creds (string) ──────────────────────

    def test_generate_signed_data_tokens_from_creds(self):
        options = {"data_tokens": ["token1", "token2"]}
        result = generate_signed_data_tokens_from_creds(VALID_CREDENTIALS_STRING, options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_creds_with_invalid_string(self):
        options = {"data_tokens": ["token1", "token2"]}
        with self.assertRaises(SkyflowError) as context:
            generate_signed_data_tokens_from_creds("{", options)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value)

    def test_generate_signed_data_tokens_from_creds_with_dict_ctx(self):
        options = {"data_tokens": ["token1"], "ctx": {"role": "admin", "level": 3}}
        result = generate_signed_data_tokens_from_creds(VALID_CREDENTIALS_STRING, options)
        self.assertEqual(len(result), 1)

    # ── snake_case end-to-end ─────────────────────────────────────────────────

    def test_generate_signed_data_tokens_with_snake_creds_file(self):
        """generate_signed_data_tokens reads the file (camelCase) but the normalize fn is a no-op for camelCase."""
        options = {"data_tokens": ["token1", "token2"]}
        result = generate_signed_data_tokens(creds_path, options)
        self.assertEqual(len(result), 2)

    def test_generate_signed_data_tokens_from_creds_snake(self):
        result = generate_signed_data_tokens_from_creds(SNAKE_CASE_CREDS_STRING, options={"data_tokens": ["t1"]})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    # ── _normalize_credentials ────────────────────────────────────────────────

    def test_normalize_credentials_snake_case(self):
        snake = {
            "private_key": "pk",
            "client_id": "cid",
            "key_id": "kid",
            "token_uri": "https://uri",
            "client_name": "name",
        }
        result = _normalize_credentials(snake)
        self.assertEqual(result["privateKey"], "pk")
        self.assertEqual(result["clientID"], "cid")
        self.assertEqual(result["keyID"], "kid")
        self.assertEqual(result["tokenURI"], "https://uri")
        self.assertEqual(result["clientName"], "name")
        self.assertNotIn("private_key", result)
        self.assertNotIn("client_id", result)
        self.assertNotIn("key_id", result)
        self.assertNotIn("token_uri", result)
        self.assertNotIn("client_name", result)

    def test_normalize_credentials_camel_case_unchanged(self):
        camel = {
            "privateKey": "pk",
            "clientID": "cid",
            "keyID": "kid",
            "tokenURI": "https://uri",
        }
        result = _normalize_credentials(camel)
        self.assertEqual(result, camel)

    def test_normalize_credentials_mixed_keys(self):
        mixed = {
            "private_key": "pk",
            "clientID": "cid",
            "key_id": "kid",
            "tokenURI": "https://uri",
        }
        result = _normalize_credentials(mixed)
        self.assertEqual(result["privateKey"], "pk")
        self.assertEqual(result["clientID"], "cid")
        self.assertEqual(result["keyID"], "kid")
        self.assertEqual(result["tokenURI"], "https://uri")
        self.assertNotIn("private_key", result)
        self.assertNotIn("key_id", result)

    def test_normalize_credentials_unknown_key_passes_through(self):
        creds = {"unknown_field": "value", "anotherField": "val2"}
        result = _normalize_credentials(creds)
        self.assertEqual(result["unknown_field"], "value")
        self.assertEqual(result["anotherField"], "val2")

    def test_normalize_credentials_empty_dict(self):
        self.assertEqual(_normalize_credentials({}), {})

    # ── _validate_and_resolve_ctx ─────────────────────────────────────────────

    def test_validate_and_resolve_ctx_none(self):
        self.assertIsNone(_validate_and_resolve_ctx(None))

    def test_validate_and_resolve_ctx_empty_string(self):
        self.assertIsNone(_validate_and_resolve_ctx(""))
        self.assertIsNone(_validate_and_resolve_ctx("   "))

    def test_validate_and_resolve_ctx_valid_string(self):
        self.assertEqual(_validate_and_resolve_ctx("user_12345"), "user_12345")

    def test_validate_and_resolve_ctx_empty_dict(self):
        self.assertIsNone(_validate_and_resolve_ctx({}))

    def test_validate_and_resolve_ctx_valid_dict(self):
        ctx = {"role": "admin", "department": "finance"}
        self.assertEqual(_validate_and_resolve_ctx(ctx), ctx)

    def test_validate_and_resolve_ctx_dict_with_alphanumeric_keys(self):
        ctx = {"role_1": "admin", "dept2": "finance", "ABC_123": "value"}
        self.assertEqual(_validate_and_resolve_ctx(ctx), ctx)

    def test_validate_and_resolve_ctx_dict_with_invalid_key_hyphen(self):
        with self.assertRaises(SkyflowError):
            _validate_and_resolve_ctx({"valid_key": "value", "invalid-key": "value"})

    def test_validate_and_resolve_ctx_dict_with_invalid_key_space(self):
        with self.assertRaises(SkyflowError):
            _validate_and_resolve_ctx({"invalid key": "value"})

    def test_validate_and_resolve_ctx_dict_with_invalid_key_dot(self):
        with self.assertRaises(SkyflowError):
            _validate_and_resolve_ctx({"invalid.key": "value"})

    def test_validate_and_resolve_ctx_valid_type_int(self):
        self.assertEqual(_validate_and_resolve_ctx(42), 42)

    def test_validate_and_resolve_ctx_valid_type_float(self):
        self.assertEqual(_validate_and_resolve_ctx(3.14), 3.14)

    def test_validate_and_resolve_ctx_valid_type_bool_true(self):
        self.assertEqual(_validate_and_resolve_ctx(True), True)

    def test_validate_and_resolve_ctx_valid_type_bool_false(self):
        self.assertEqual(_validate_and_resolve_ctx(False), False)

    def test_validate_and_resolve_ctx_invalid_type_list(self):
        with self.assertRaises(SkyflowError):
            _validate_and_resolve_ctx(["a", "b"])

    def test_validate_and_resolve_ctx_dict_with_mixed_value_types(self):
        ctx = {"role": "admin", "level": 3, "active": True, "timestamp": "2025-12-25T10:30:00Z"}
        self.assertEqual(_validate_and_resolve_ctx(ctx), ctx)

    def test_validate_and_resolve_ctx_dict_with_nested_objects(self):
        ctx = {"role": "admin", "metadata": {"level": 2, "tags": ["a", "b"]}}
        self.assertEqual(_validate_and_resolve_ctx(ctx), ctx)

    # ── additional coverage gaps ──────────────────────────────────────────────

    @patch("skyflow.service_account._utils.jwt.decode", side_effect=jwt.ExpiredSignatureError)
    def test_is_expired_expired_signature_error(self, mock_decode):
        token = jwt.encode({"exp": time.time() + 1000}, key="test", algorithm="HS256")
        self.assertTrue(is_expired(token))

    @patch("skyflow.service_account._utils.AuthClient")
    @patch("skyflow.service_account._utils.get_signed_jwt")
    def test_get_service_account_token_with_token_uri_option_override(self, mock_get_signed_jwt, mock_auth_client):
        creds = {
            "privateKey": "private_key",
            "clientID": "client_id",
            "keyID": "key_id",
            "tokenURI": "https://valid-url.com",
        }
        override_uri = "https://override-url.com"
        options = {"token_uri": override_uri}
        mock_get_signed_jwt.return_value = "signed"
        mock_auth_api = mock_auth_client.return_value.get_auth_api.return_value
        mock_auth_api.authentication_service_get_auth_token.return_value = type(
            "obj", (), {"access_token": "token", "token_type": "bearer"}
        )
        get_service_account_token(creds, options, None)
        mock_get_signed_jwt.assert_called_once()
        call_args = mock_get_signed_jwt.call_args
        self.assertEqual(call_args[0][3], override_uri)

    @patch("json.load", side_effect=json.JSONDecodeError("bad json", "", 0))
    def test_generate_signed_data_tokens_from_file_invalid_json(self, mock_load):
        invalid_path = os.path.join(os.path.dirname(__file__), "invalid_creds.json")
        with self.assertRaises(SkyflowError) as context:
            generate_signed_data_tokens(invalid_path, {"data_tokens": ["t1"]})
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.FILE_INVALID_JSON.value.format(invalid_path),
        )
