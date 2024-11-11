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

VALID_CREDENTIALS_STRING = '{"clientID":"b78eee76e91c43eda7a0e83f5c3a98e6","clientName":"test_V2","tokenURI":"https://manage.skyflowapis.dev/v1/auth/sa/oauth/token","keyID":"f927c615ca2b433294dcf45da0ba010c","privateKey":"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7iqpXXHjMuk5z\nh4PdOp6CxFr2zy6HCe2HKHzNvYcRk04jpjQgw/oRwXd8B5doMTmIzpxJ0K9sDBO4\nvYSdwjRhFnpnXWoVHKijtMUxWAuyZdB1mA/3hqeElpb6218aQeyGA6H98TTzb5G6\nJxn5lBr0qChm2o4gJHbYUO8PVvvm/ixDMrb87sH+yfCTYEWCcE9AozK3d1mST9F1\nSEnQEDML3mBTBqgLRn0NuEI273RpyAierY8KhQkiKg+0p3d2KkIrqgz05XlyKgw+\nV/ECymq2nH4vi3vGzSWMFSxiQ65fKZim+SPqIOLJZGemTOkfGv4SRWCCZ0WOLXO5\nsRcpsttpAgMBAAECggEBAKPcnsVCKNJInq9W4qJzy3fadNhdYfvfcsi7WYCybseu\ne4GugLF4SpElB285etMw32JnlCryybOQQdMS1EK7IuUJrN2Pw1a6+aZAFmPs2BuB\n1khJGvpdjxTMNxLshgX9P9pAZlPpYyiofR23eHyXKY5HNzXXFIOFGMocvSQcDnFe\neQom0mcd5EwVs5Zk4RDtLQlKdqByGgmMI/GRtdG8Of5jKhG1g3YomYAGIaFqCAEJ\nyUJEhfGMztpl8glLPECt2X09oUVrwwM7zOj3a0B46b1zmuLlcusIQHgMg9pNJBOR\nno4LAC8pMX5JEJjFRAYGsrntooHSAWR2n09GzDNkkxkCgYEA3FxZb2rOtcLQf8Dw\nC0UmcYWo3n0o4TVIjbSLPb0vKDIjkLmK42rNmMinD7BooSGPyPB/SNOm5NircDlv\nR5OVA4F3WUhMiDMPcZu/CJ5yWHNyR4y+erZh8NSbc4xwSfTdmMnclPkQBDu8N41N\n9KBwvTT8mqaIMw7NjhN0J1IM1O8CgYEA2d9/4+24GSMCltTQkGh7sALZyGhef/cR\nvL1cNMAeHzvrJVffp9rixtmVs20XCwbVH6AZXlHk5ALfSTo6XurBQyhPls6LC6ns\nNOoyviveo0fV0H8fj39wOWjZh3LQS/5CgxtBh6URMDVJfGv7NIAMOHBXVh8EyA8E\ndrks47VGRScCgYAxt1wuOQi+FV/5EsyVnlpYDnHVEKPie6UM44juuvoitX00r8fY\nG0abi9m1PnW8tNe93BS7l5T12LSFM1AZ9AAQtGr658bsi6iWVy84gJcHwbQs1GI9\nSVy7exw/a5YB+Y7tY82yhqbIbbm/RtApuvD0nznGon/kFRjnTxhLrsVaXQKBgCOH\nNbS2bCH1OpPcClKyJxFRta/fjSFy6bqMan/ToFXZkIPba4ZUxExG6QmETZCnwZNR\nqTFfS2L/MOghDamywGcyKKBf9/6j6/fJBRNL1hdsPGqugDgHQQarmWVkDKGHydLV\nW/9BpKbm2Z/nf+RUySle8G8DyeTRxhmSIsbTJa1bAoGBAMD6TXQg15dX9+hltpMh\n16IJB6Y15AA9KEiVKDyD+WF4V7BVIbsMmjFGoNBAF5/uwJk5UVKaGHjP5Dl12InR\n38wOrDi+uuOGlDfsiPJZ91reGdoXVNAfky9sRK1uBiRiskaWliP4hLdb1SsUzu5s\nHbxRby/7eC3gvCVA+6LqV9Fv\n-----END PRIVATE KEY-----\n","keyValidAfterTime":"2024-10-21T18:06:26.000Z","keyValidBeforeTime":"2025-10-21T18:06:26.000Z","keyAlgorithm":"KEY_ALG_RSA_2048"}'

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

VALID_SERVICE_ACCOUNT_CREDS = {"clientID":"b78eee76e91c43eda7a0e83f5c3a98e6","clientName":"test_V2","tokenURI":"https://manage.skyflowapis.dev/v1/auth/sa/oauth/token","keyID":"f927c615ca2b433294dcf45da0ba010c","privateKey":"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7iqpXXHjMuk5z\nh4PdOp6CxFr2zy6HCe2HKHzNvYcRk04jpjQgw/oRwXd8B5doMTmIzpxJ0K9sDBO4\nvYSdwjRhFnpnXWoVHKijtMUxWAuyZdB1mA/3hqeElpb6218aQeyGA6H98TTzb5G6\nJxn5lBr0qChm2o4gJHbYUO8PVvvm/ixDMrb87sH+yfCTYEWCcE9AozK3d1mST9F1\nSEnQEDML3mBTBqgLRn0NuEI273RpyAierY8KhQkiKg+0p3d2KkIrqgz05XlyKgw+\nV/ECymq2nH4vi3vGzSWMFSxiQ65fKZim+SPqIOLJZGemTOkfGv4SRWCCZ0WOLXO5\nsRcpsttpAgMBAAECggEBAKPcnsVCKNJInq9W4qJzy3fadNhdYfvfcsi7WYCybseu\ne4GugLF4SpElB285etMw32JnlCryybOQQdMS1EK7IuUJrN2Pw1a6+aZAFmPs2BuB\n1khJGvpdjxTMNxLshgX9P9pAZlPpYyiofR23eHyXKY5HNzXXFIOFGMocvSQcDnFe\neQom0mcd5EwVs5Zk4RDtLQlKdqByGgmMI/GRtdG8Of5jKhG1g3YomYAGIaFqCAEJ\nyUJEhfGMztpl8glLPECt2X09oUVrwwM7zOj3a0B46b1zmuLlcusIQHgMg9pNJBOR\nno4LAC8pMX5JEJjFRAYGsrntooHSAWR2n09GzDNkkxkCgYEA3FxZb2rOtcLQf8Dw\nC0UmcYWo3n0o4TVIjbSLPb0vKDIjkLmK42rNmMinD7BooSGPyPB/SNOm5NircDlv\nR5OVA4F3WUhMiDMPcZu/CJ5yWHNyR4y+erZh8NSbc4xwSfTdmMnclPkQBDu8N41N\n9KBwvTT8mqaIMw7NjhN0J1IM1O8CgYEA2d9/4+24GSMCltTQkGh7sALZyGhef/cR\nvL1cNMAeHzvrJVffp9rixtmVs20XCwbVH6AZXlHk5ALfSTo6XurBQyhPls6LC6ns\nNOoyviveo0fV0H8fj39wOWjZh3LQS/5CgxtBh6URMDVJfGv7NIAMOHBXVh8EyA8E\ndrks47VGRScCgYAxt1wuOQi+FV/5EsyVnlpYDnHVEKPie6UM44juuvoitX00r8fY\nG0abi9m1PnW8tNe93BS7l5T12LSFM1AZ9AAQtGr658bsi6iWVy84gJcHwbQs1GI9\nSVy7exw/a5YB+Y7tY82yhqbIbbm/RtApuvD0nznGon/kFRjnTxhLrsVaXQKBgCOH\nNbS2bCH1OpPcClKyJxFRta/fjSFy6bqMan/ToFXZkIPba4ZUxExG6QmETZCnwZNR\nqTFfS2L/MOghDamywGcyKKBf9/6j6/fJBRNL1hdsPGqugDgHQQarmWVkDKGHydLV\nW/9BpKbm2Z/nf+RUySle8G8DyeTRxhmSIsbTJa1bAoGBAMD6TXQg15dX9+hltpMh\n16IJB6Y15AA9KEiVKDyD+WF4V7BVIbsMmjFGoNBAF5/uwJk5UVKaGHjP5Dl12InR\n38wOrDi+uuOGlDfsiPJZ91reGdoXVNAfky9sRK1uBiRiskaWliP4hLdb1SsUzu5s\nHbxRby/7eC3gvCVA+6LqV9Fv\n-----END PRIVATE KEY-----\n","keyValidAfterTime":"2024-10-21T18:06:26.000Z","keyValidBeforeTime":"2025-10-21T18:06:26.000Z","keyAlgorithm":"KEY_ALG_RSA_2048"}

# utils constants

VALID_URL = "https://example.com/path?query=1"
BASE_URL = "https://example.com"
INVALID_URL = "invalid-url"
EMPTY_URL = ""
SCOPES_LIST = ["admin", "user", "viewer"]
FORMATTED_SCOPES = "role:admin role:user role:viewer"
INVALID_JSON_FORMAT = '{"invalid": json}'

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


