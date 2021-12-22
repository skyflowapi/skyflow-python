from enum import Enum
from skyflow._utils import log_error

class SkyflowErrorCodes(Enum):
    INVALID_INPUT = 400
    SERVER_ERROR = 500
    PARTIAL_SUCCESS = 500

class SkyflowErrorMessages(Enum):
    FILE_NOT_FOUND = "File at %s not found"
    FILE_INVALID_JSON = "File at %s is not in JSON format"
    INVALID_CREDENTIALS = "Given credentials are not valid"
    INVALID_URL = "Given url '%s' is invalid"

    MISSING_PRIVATE_KEY = "Unable to read Private key"
    MISSING_CLIENT_ID = "Unable to read Client ID"
    MISSING_KEY_ID = "Unable to read Key ID"
    MISSING_TOKEN_URI = "Unable to read Token URI"

    JWT_INVALID_FORMAT = "Private key is not in correct format"
    MISSING_ACCESS_TOKEN = "accessToken not present in response"
    MISSING_TOKEN_TYPE = "tokenType not present in response"

    # vault
    RECORDS_KEY_ERROR = "Records key is missing from payload"
    FIELDS_KEY_ERROR = "Fields key is missing from payload"
    TABLE_KEY_ERROR = "Table key is missing from payload"
    TOKEN_KEY_ERROR = "Token key is missing from payload"
    IDS_KEY_ERROR = "Ids key is missing from payload"
    REDACTION_KEY_ERROR = "Redaction key is missing from payload"

    INVALID_JSON = "Given %s is invalid JSON"
    INVALID_RECORDS_TYPE = "Records key has value of type %s, expected list"
    INVALID_FIELDS_TYPE = "Fields key has value of type %s, expected string"
    INVALID_TABLE_TYPE = "Table key has value of type %s, expected string"
    INVALID_IDS_TYPE = "Ids key has value of type %s, expected list"
    INVALID_ID_TYPE = "Id key has value of type %s, expected string"
    INVALID_REDACTION_TYPE = "Redaction key has value of type %s, expected Skyflow.Redaction"

    INVALID_REQUEST_BODY = "Given request body is not valid"
    INVALID_HEADERS = "Given Request Headers is not valid"
    INVALID_PATH_PARAMS = "Given path params are not valid"
    INVALID_QUERY_PARAMS = "Given query params are not valid"
    INVALID_PATH_PARAM_TYPE = "Path params (key, value) must be of type 'str' given type - (%s, %s)"
    INVALID_QUERY_PARAM_TYPE = "Query params (key, value) must be of type 'str' given type - (%s, %s)"


    INVALID_TOKEN_TYPE = "Token key has value of type %s, expected string"
    PARTIAL_SUCCESS = "Server returned errors, check SkyflowError.data for more"

    VAULT_ID_INVALID_TYPE = "Expected Vault ID to be str, got %s"
    VAULT_URL_INVALID_TYPE = "Expected Vault URL to be str, got %s"
    TOKEN_PROVIDER_ERROR = "Expected Token Provider to be function, got %s"

    EMPTY_VAULT_ID = "Vault ID must not be empty"
    EMPTY_VAULT_URL = "Vault URL must not be empty"

class SkyflowError(Exception):
    def __init__(self, code, message="An Error occured", data={}, interface: str=None) -> None:
        if type(code) is SkyflowErrorCodes:
            self.code = code.value
        else:
            self.code = code
        if type(message) is SkyflowErrorMessages:
            self.message = message.value
        else:
            self.message = message
        log_error(self.message, interface)
        self.data = data
        super().__init__(self.message)

