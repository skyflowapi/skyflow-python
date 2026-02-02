import json
import datetime
import time
import jwt
from skyflow.error import SkyflowError
from skyflow.service_account.client.auth_client import AuthClient
from skyflow.utils.logger import log_info, log_error_log
from skyflow.utils import get_base_url, format_scope, SkyflowMessages
from skyflow.utils.constants import JWT, CredentialField, JwtField, OptionField, ResponseField


invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def is_expired(token, logger = None):
    if len(token) == 0:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_BEARER_TOKEN.value)
        return True

    try:
        decoded = jwt.decode(
            token, options={OptionField.VERIFY_SIGNATURE: False, OptionField.VERIFY_AUD: False})
        if time.time() >= decoded[JwtField.EXP]:
            log_info(SkyflowMessages.Info.BEARER_TOKEN_EXPIRED.value, logger)
            log_error_log(SkyflowMessages.ErrorLogs.INVALID_BEARER_TOKEN.value)
            return True
        return False
    except jwt.ExpiredSignatureError:
        return True
    except Exception:
        log_error_log(SkyflowMessages.Error.JWT_DECODE_ERROR.value, logger)
        return True

def generate_bearer_token(credentials_file_path, options = None, logger = None):
    try:
        log_info(SkyflowMessages.Info.GET_BEARER_TOKEN_TRIGGERED.value, logger)
        with open(credentials_file_path, 'r') as credentials_file:
            try:
                credentials = json.load(credentials_file)
            except Exception:
                log_error_log(SkyflowMessages.ErrorLogs.INVALID_CREDENTIALS_FILE.value, logger = logger)
                raise SkyflowError(SkyflowMessages.Error.FILE_INVALID_JSON.value.format(credentials_file_path), invalid_input_error_code)
    except OSError:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value, invalid_input_error_code)
    
    result = get_service_account_token(credentials, options, logger)
    return result

def generate_bearer_token_from_creds(credentials, options = None, logger = None):
    log_info(SkyflowMessages.Info.GET_BEARER_TOKEN_TRIGGERED.value, logger)
    credentials = credentials.strip()
    try:
        json_credentials = json.loads(credentials.replace('\n', '\\n'))
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value, invalid_input_error_code)
    result = get_service_account_token(json_credentials, options, logger)
    return result

def get_service_account_token(credentials, options, logger):
    try:
        private_key = credentials[CredentialField.PRIVATE_KEY]
    except:
        log_error_log(SkyflowMessages.ErrorLogs.PRIVATE_KEY_IS_REQUIRED.value, logger = logger)
        raise SkyflowError(SkyflowMessages.Error.MISSING_PRIVATE_KEY.value, invalid_input_error_code)
    try:
        client_id = credentials[CredentialField.CLIENT_ID]
    except:
        log_error_log(SkyflowMessages.ErrorLogs.CLIENT_ID_IS_REQUIRED.value, logger=logger)
        raise SkyflowError(SkyflowMessages.Error.MISSING_CLIENT_ID.value, invalid_input_error_code)
    try:
        key_id = credentials[CredentialField.KEY_ID]
    except:
        log_error_log(SkyflowMessages.ErrorLogs.KEY_ID_IS_REQUIRED.value, logger=logger)
        raise SkyflowError(SkyflowMessages.Error.MISSING_KEY_ID.value, invalid_input_error_code)
    try:
        token_uri = credentials[CredentialField.TOKEN_URI]
    except:
        log_error_log(SkyflowMessages.ErrorLogs.TOKEN_URI_IS_REQUIRED.value, logger=logger)
        raise SkyflowError(SkyflowMessages.Error.MISSING_TOKEN_URI.value, invalid_input_error_code)

    signed_token = get_signed_jwt(options, client_id, key_id, token_uri, private_key, logger)
    base_url = get_base_url(token_uri)
    auth_client = AuthClient(base_url)
    auth_api = auth_client.get_auth_api()

    formatted_scope = None
    if options and OptionField.ROLE_IDS in options:
        formatted_scope = format_scope(options.get(OptionField.ROLE_IDS))

    response = auth_api.authentication_service_get_auth_token(assertion = signed_token,
                                    grant_type=JWT.GRANT_TYPE_JWT_BEARER,
                                    scope=formatted_scope)
    log_info(SkyflowMessages.Info.GET_BEARER_TOKEN_SUCCESS.value, logger)
    return response.access_token, response.token_type

def get_signed_jwt(options, client_id, key_id, token_uri, private_key, logger):
    payload = {
        JwtField.ISS: client_id,
        JwtField.KEY: key_id,
        JwtField.AUD: token_uri,
        JwtField.SUB: client_id,
        JwtField.EXP: datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    if options and JwtField.CTX in options:
        payload[JwtField.CTX] = options.get(JwtField.CTX)
    try:
        return jwt.encode(payload=payload, key=private_key, algorithm=JWT.ALGORITHM_RS256)
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.JWT_INVALID_FORMAT.value, invalid_input_error_code)



def get_signed_tokens(credentials_obj, options):
    try:
        expiry_time = int(time.time()) + options.get(OptionField.TIME_TO_LIVE, 60)
        prefix = JWT.SIGNED_TOKEN_PREFIX

        if options and options.get(OptionField.DATA_TOKENS):
            for token in options[OptionField.DATA_TOKENS]:
                claims = {
                    JwtField.ISS: JWT.ISSUER_SDK,
                    JwtField.KEY: credentials_obj.get(CredentialField.KEY_ID),
                    JwtField.EXP: expiry_time,
                    JwtField.SUB: credentials_obj.get(CredentialField.CLIENT_ID),
                    JwtField.TOK: token,
                    JwtField.IAT: int(time.time()),
                }

                if JwtField.CTX in options:
                    claims[JwtField.CTX] = options[JwtField.CTX]

                private_key = credentials_obj.get(CredentialField.PRIVATE_KEY)
                signed_jwt = jwt.encode(claims, private_key, algorithm=JWT.ALGORITHM_RS256)
                response_object = get_signed_data_token_response_object(prefix + signed_jwt, token)
        log_info(SkyflowMessages.Info.GET_SIGNED_DATA_TOKEN_SUCCESS.value)
        return response_object

    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS.value, invalid_input_error_code)


def generate_signed_data_tokens(credentials_file_path, options):
    log_info(SkyflowMessages.Info.GET_SIGNED_DATA_TOKENS_TRIGGERED.value)
    try:
        with open(credentials_file_path, 'r') as credentials_file:
            try:
                credentials = json.load(credentials_file)
            except Exception:
                raise SkyflowError(SkyflowMessages.Error.FILE_INVALID_JSON.value.format(credentials_file_path),
                                   invalid_input_error_code)
    except FileNotFoundError:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value, invalid_input_error_code)

    return get_signed_tokens(credentials, options)

def generate_signed_data_tokens_from_creds(credentials, options):
    log_info(SkyflowMessages.Info.GET_SIGNED_DATA_TOKENS_TRIGGERED.value)
    credentials = credentials.strip()
    try:
        json_credentials = json.loads(credentials.replace('\n', '\\n'))
    except Exception:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_CREDENTIALS_FILE.value)
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value, invalid_input_error_code)
    return get_signed_tokens(json_credentials, options)

def get_signed_data_token_response_object(signed_token, actual_token):
    response_object = {
        ResponseField.TOKEN: actual_token,
        ResponseField.SIGNED_TOKEN: signed_token
    }
    return response_object.get(ResponseField.TOKEN), response_object.get(ResponseField.SIGNED_TOKEN)
