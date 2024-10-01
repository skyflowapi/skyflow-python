import json
import datetime
import jwt
from skyflow.error import SkyflowError
from skyflow.generated.rest.models import V1GetAuthTokenRequest
from skyflow.service_account.client.auth_client import AuthClient
from skyflow.utils import get_base_url, format_scope


def generate_bearer_token(credentials_file_path, roles = None):
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

    result = get_service_account_token(credentials, roles)

    return result


def generate_bearer_token_from_creds(credentials, roles = None):
    try:
        json_credentials = json.loads(credentials.replace('\n', '\\n'))
    except Exception as e:
        raise SkyflowError(e)
    result = get_service_account_token(json_credentials, roles)
    return result

def get_service_account_token(credentials, roles):
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

    signed_token = get_signed_jwt(client_id, key_id, token_uri, private_key)
    base_url = get_base_url(token_uri)
    auth_client = AuthClient(base_url)
    auth_api = auth_client.get_auth_api()

    formatted_scope = format_scope(roles)
    request = V1GetAuthTokenRequest(assertion = signed_token,
                                    grant_type="urn:ietf:params:oauth:grant-type:jwt-bearer",
                                    scope=formatted_scope)
    response = auth_api.authentication_service_get_auth_token(request)
    return response.access_token


def get_signed_jwt(client_id, key_id, token_uri, private_key):
    payload = {
        "iss": client_id,
        "key": key_id,
        "aud": token_uri,
        "sub": client_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    try:
        return jwt.encode(payload=payload, key=private_key, algorithm="RS256")
    except Exception as e:
        raise SkyflowError("")