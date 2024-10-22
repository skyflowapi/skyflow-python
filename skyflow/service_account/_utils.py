import json
import datetime
import time
import jwt
from skyflow.error import SkyflowError
from skyflow.generated.rest.models import V1GetAuthTokenRequest
from skyflow.service_account.client.auth_client import AuthClient
from skyflow.utils.logger import log_error
from skyflow.utils import get_base_url, format_scope, SkyflowMessages


invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def is_expired(token, logger = None):
    if len(token) == 0:
        return True

    try:
        decoded = jwt.decode(
            token, options={"verify_signature": False, "verify_aud": False})
        if time.time() < decoded['exp']:
            return False
    except jwt.ExpiredSignatureError:
        return True
    except Exception:
        log_error(SkyflowMessages.Error.JWT_DECODE_ERROR.value, invalid_input_error_code, logger = logger)
        return True
    pass

import re

def validate_api_key(api_key: str) -> bool:
    if len(api_key) != 42:
        return False
    api_key_pattern = re.compile(r'^sky-[a-zA-Z0-9]{5}-[a-fA-F0-9]{32}$')

    return bool(api_key_pattern.match(api_key))


def generate_bearer_token(credentials_file_path, options = None, logger = None):
    try:
        credentials_file =open(credentials_file_path, 'r')
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value, invalid_input_error_code, logger = logger)

    try:
        credentials = json.load(credentials_file)
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.FILE_INVALID_JSON.value.format(credentials_file_path), invalid_input_error_code, logger = logger)

    finally:
        credentials_file.close()
    result = get_service_account_token(credentials, options, logger)
    return result

def generate_bearer_token_from_creds(credentials, options = None, logger = None):
    credentials = credentials.strip()
    try:
        json_credentials = json.loads(credentials.replace('\n', '\\n'))
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value, invalid_input_error_code, logger = logger)
    result = get_service_account_token(json_credentials, options, logger)
    return result

def get_service_account_token(credentials, options, logger):
    try:
        private_key = credentials["privateKey"]
    except:
        raise SkyflowError(SkyflowMessages.Error.MISSING_PRIVATE_KEY.value, invalid_input_error_code, logger = logger)
    try:
        client_id = credentials["clientID"]
    except:
        raise SkyflowError(SkyflowMessages.Error.MISSING_CLIENT_ID.value, invalid_input_error_code, logger = logger)
    try:
        key_id = credentials["keyID"]
    except:
        raise SkyflowError(SkyflowMessages.Error.MISSING_KEY_ID.value, invalid_input_error_code, logger = logger)
    try:
        token_uri = credentials["tokenURI"]
    except:
        raise SkyflowError(SkyflowMessages.Error.MISSING_TOKEN_URI.value, invalid_input_error_code, logger = logger)

    signed_token = get_signed_jwt(options, client_id, key_id, token_uri, private_key, logger)
    base_url = get_base_url(token_uri)
    auth_client = AuthClient(base_url)
    auth_api = auth_client.get_auth_api()

    formatted_scope = None
    if options and "role_ids" in options:
        formatted_scope = format_scope(options.get("role_ids"))

    request = V1GetAuthTokenRequest(assertion = signed_token,
                                    grant_type="urn:ietf:params:oauth:grant-type:jwt-bearer",
                                    scope=formatted_scope)
    response = auth_api.authentication_service_get_auth_token(request)
    return response.access_token, response.token_type

def get_signed_jwt(options, client_id, key_id, token_uri, private_key, logger):
    payload = {
        "iss": client_id,
        "key": key_id,
        "aud": token_uri,
        "sub": client_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    if options and "ctx" in options:
        payload["ctx"] = options.get("ctx")
    try:
        return jwt.encode(payload=payload, key=private_key, algorithm="RS256")
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.JWT_INVALID_FORMAT.value, invalid_input_error_code, logger = logger)



def get_signed_tokens(credentials, options):
    try:
        try:
            credentials_obj = json.loads(credentials)
        except:
            raise  ValueError("Invalid JSON")

        expiry_time = time.time() + options.get("time_to_live", 60)
        prefix = "signed_token_"
        response_array=[]

        if options and options.get("data_tokens"):
            for token in options["data_tokens"]:
                claims = {
                    "iss": "sdk",
                    "key": credentials_obj.get("keyID"),
                    "aud": credentials_obj.get("tokenURI"),
                    "exp": expiry_time,
                    "sub": credentials_obj.get("clientID"),
                    "tok": token
                }

                if "ctx" in options:
                    claims["ctx"] = options["ctx"]

                private_key = credentials_obj.get("privateKey")
                signed_jwt = jwt.encode(claims, private_key, algorithm="RS256")
                response_object = get_signed_data_token_response_object(prefix + signed_jwt, token)
                response_array.append(response_object)

        return response_array

    except Exception as e:
        raise ValueError(str(e))


def generate_signed_data_tokens(credentials_file_path, options, logger = None):
    try:
        credentials_file =open(credentials_file_path, 'r')
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value, invalid_input_error_code, logger = logger)

    return get_signed_tokens(credentials_file, options)

def generate_signed_data_tokens_from_creds(credentials, options):
    return get_signed_tokens(credentials, options)

def get_signed_data_token_response_object(signed_token, actual_token):
    response_object = {
        "token": actual_token,
        "signed_token": signed_token
    }
    return response_object
