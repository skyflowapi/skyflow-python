import json
import datetime
import time
import jwt
from skyflow.error import SkyflowError
from skyflow.generated.rest.models import V1GetAuthTokenRequest
from skyflow.service_account.client.auth_client import AuthClient
from skyflow.utils import get_base_url, format_scope

def is_expired(token):
    if len(token) == 0:
        return True

    try:
        decoded = jwt.decode(
            token, options={"verify_signature": False, "verify_aud": False})
        if time.time() < decoded['exp']:
            return False
    except jwt.ExpiredSignatureError:
        return True
    except Exception as e:
        SkyflowError("Invalid token")
        return True
    pass

def generate_bearer_token(credentials_file_path, options = None):
    try:
        credentials_file =open(credentials_file_path, 'r')
    except Exception:
        raise SkyflowError("Invalid file path")

    try:
        credentials = json.load(credentials_file)
    except Exception:
        raise SkyflowError("Error in json parsing")

    finally:
        credentials_file.close()
    result = get_service_account_token(credentials, options)
    return result

def generate_bearer_token_from_creds(credentials, options = None):
    try:
        json_credentials = json.loads(credentials.replace('\n', '\\n'))
    except Exception as e:
        raise SkyflowError(e)
    result = get_service_account_token(json_credentials, options)
    return result

def get_service_account_token(credentials, options):
    try:
        private_key = credentials["privateKey"]
    except:
        raise SkyflowError("privateKey not found")
    try:
        client_id = credentials["clientID"]
    except:
        raise SkyflowError("clientID not found")
    try:
        key_id = credentials["keyID"]
    except:
        raise SkyflowError("keyID not found")
    try:
        token_uri = credentials["tokenURI"]
    except:
        raise SkyflowError("tokenURI not found")

    signed_token = get_signed_jwt(options, client_id, key_id, token_uri, private_key)
    base_url = get_base_url(token_uri)
    auth_client = AuthClient(base_url)
    auth_api = auth_client.get_auth_api()

    formatted_scope = None
    if "role_ids" in options:
        formatted_scope = format_scope(options.get("role_ids"))

    request = V1GetAuthTokenRequest(assertion = signed_token,
                                    grant_type="urn:ietf:params:oauth:grant-type:jwt-bearer",
                                    scope=formatted_scope)
    response = auth_api.authentication_service_get_auth_token(request)
    return response.access_token, response.token_type

def get_signed_jwt(options, client_id, key_id, token_uri, private_key):
    payload = {
        "iss": client_id,
        "key": key_id,
        "aud": token_uri,
        "sub": client_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    if "ctx" in options:
        payload["ctx"] = options.get("ctx")
    try:
        return jwt.encode(payload=payload, key=private_key, algorithm="RS256")
    except Exception as e:
        raise SkyflowError("")



def get_signed_tokens(credentials, options):
    try:
        try:
            credentials_obj = json.loads(credentials)
        except:
            raise  SkyflowError("Invalid JSON")

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
        raise SkyflowError(str(e))


def generate_signed_data_tokens(credentials_file_path, options):
    try:
        credentials_file =open(credentials_file_path, 'r')
    except Exception:
        raise SkyflowError("Invalid file path")

    return get_signed_tokens(credentials_file_path, options)

def generate_signed_data_tokens_from_creds(credentials, options):
    return get_signed_tokens(credentials, options)

def get_signed_data_token_response_object(signed_token, actual_token):
    response_object = {
        "token": actual_token,
        "signed_token": signed_token
    }
    return response_object
