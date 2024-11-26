from skyflow import LogLevel
from skyflow import  Env

#client initialization constants

VALID_VAULT_CONFIG = {
    "vault_id": "d3dd9bbb7abc4c779b72f32cb7ee5d14",
    "cluster_id": "sb.area51",
    "env": Env.DEV,
    "credentials": {"path": "/path/to/valid_credentials.json"}
}

INVALID_VAULT_CONFIG = {
    "cluster_id": "sb.area51",  # Missing vault_id
    "env": Env.DEV,
    "credentials": {"path": "/path/to/valid_credentials.json"}
}


VALID_CONNECTION_CONFIG = {
    "connection_id": "ef34fc6b0b914ad59a1754c06f10b24c",
    "connection_url": "https://sb.area51.gateway.skyflowapis.dev/v1/gateway/inboundRoutes/ef34fc6b0b914ad59a1754c06f10b24c/test",
    "credentials": {"path": "/path/to/valid_credentials.json"}
}

INVALID_CONNECTION_CONFIG = {
    "connection_url": "https://sb.area51.gateway.skyflowapis.dev/v1/gateway/inboundRoutes/ef34fc6b0b914ad59a1754c06f10b24c/test",
    # Missing connection_id
    "credentials": {"path": "/path/to/valid_credentials.json"}
}

VALID_LOG_LEVEL = LogLevel.INFO
INVALID_LOG_LEVEL = "INVALID_LOG_LEVEL"
VALID_CREDENTIALS = {
    "path": "/path/to/valid_credentials.json"
}

# service account constants

VALID_CREDENTIALS_STRING = ''

VALID_SERVICE_ACCOUNT_CREDS = {}

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

# utils constants

VALID_URL = "https://example.com/path?query=1"
BASE_URL = "https://example.com"
INVALID_URL = "invalid-url"
EMPTY_URL = ""
SCOPES_LIST = ["admin", "user", "viewer"]
FORMATTED_SCOPES = "role:admin role:user role:viewer"
INVALID_JSON_FORMAT = '[{"invalid": "json"}]'

TEST_ERROR_MESSAGE = "Test error message."


# vault controller constants

VAULT_ID = "test_vault_id"
TABLE_NAME = "test_table"

# vault client constants

CONFIG = {
    "credentials": "some_credentials",
    "cluster_id": "test_cluster_id",
    "env": "test_env",
    "vault_id": "test_vault_id",
    "roles": ["role_id_1", "role_id_2"],
    "ctx": "context"
}

CREDENTIALS_WITH_API_KEY = {"api_key": "dummy_api_key"}
CREDENTIALS_WITH_TOKEN = {"token": "dummy_token"}
CREDENTIALS_WITH_PATH = {"path": "/path/to/creds.json"}
CREDENTIALS_WITH_STRING = {"credentials_string": "dummy_credentials_string"}

VALID_ENV_CREDENTIALS = {"clientID":"CLIENT_ID","clientName":"test_V2","tokenURI":"TOKEN_URI","keyID":"KEY_ID","privateKey":"PRIVATE_KEY","keyValidAfterTime":"2024-10-21T18:06:26.000Z","keyValidBeforeTime":"2025-10-21T18:06:26.000Z","keyAlgorithm":"KEY_ALG_RSA_2048"}


# connection controller constants

# test_constants.py

VAULT_CONFIG = {
    "credentials": {"api_key": "test_api_key"},
    "connection_url": "https://vault.skyflow.com/connection"
}
VALID_PATH_PARAMS = {"path_key": "value"}
VALID_HEADERS = {"Content-Type": "application/json"}
VALID_BODY = {"key": "value"}
VALID_QUERY_PARAMS = {"query_key": "value"}
INVALID_HEADERS = "invalid_headers"
INVALID_BODY = "invalid_body"
VALID_BEARER_TOKEN = "test_bearer_token"
SUCCESS_STATUS_CODE = 200
FAILURE_STATUS_CODE = 400
SUCCESS_RESPONSE_CONTENT = '{"response": "success"}'
ERROR_RESPONSE_CONTENT = '{"error": {"message": "error occurred"}}'


