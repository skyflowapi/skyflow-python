'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from enum import Enum
from skyflow._utils import log_error


class SkyflowErrorCodes(Enum):
    INVALID_INPUT = 400
    INVALID_INDEX = 404
    SERVER_ERROR = 500
    PARTIAL_SUCCESS = 500


class SkyflowErrorMessages(Enum):
    API_ERROR = "Server returned status code %s"

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
    JWT_DECODE_ERROR = "Invalid access token"

    # vault
    RECORDS_KEY_ERROR = "Records key is missing from payload"
    FIELDS_KEY_ERROR = "Fields key is missing from payload"
    TABLE_KEY_ERROR = "Table key is missing from payload"
    TOKEN_KEY_ERROR = "Token key is missing from payload"
    IDS_KEY_ERROR = "Id(s) key is missing from payload"
    REDACTION_KEY_ERROR = "Redaction key is missing from payload"
    UNIQUE_COLUMN_OR_IDS_KEY_ERROR = "Ids or Unique column key is missing from payload"
    UPDATE_FIELD_KEY_ERROR = "Atleast one field should be provided to update"

    INVALID_JSON = "Given %s is invalid JSON"
    INVALID_RECORDS_TYPE = "Records key has value of type %s, expected list"
    INVALID_FIELDS_TYPE = "Fields key has value of type %s, expected dict"
    INVALID_TABLE_TYPE = "Table key has value of type %s, expected string"
    INVALID_TABLE_TYPE_DELETE = "Table of type string is required at index %s in records array"
    INVALID_IDS_TYPE = "Ids key has value of type %s, expected list"
    INVALID_ID_TYPE = "Id key has value of type %s, expected string"
    INVALID_ID_TYPE_DELETE = "Id of type string is required at index %s in records array"
    INVALID_REDACTION_TYPE = "Redaction key has value of type %s, expected Skyflow.Redaction"
    INVALID_COLUMN_NAME = "Column name has value of type %s, expected string"
    INVALID_COLUMN_VALUE = "Column values has value of type %s, expected list"
    EMPTY_RECORDS_IN_DELETE = "records array cannot be empty"
    EMPTY_ID_IN_DELETE = "Id cannot be empty in records array"
    EMPTY_TABLE_IN_DELETE = "Table cannot be empty in records array"
    RECORDS_KEY_NOT_FOUND_DELETE = "records object is required"

    INVALID_REQUEST_BODY = "Given request body is not valid"
    INVALID_RESPONSE_BODY = "Given response body is not valid"
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
    RESPONSE_NOT_JSON = "Response %s is not valid JSON"

    TOKEN_PROVIDER_INVALID_TOKEN = "Invalid token from tokenProvider"
    INVALID_UPSERT_OPTIONS_TYPE = "upsertOptions key has value of type %s, expected list"
    EMPTY_UPSERT_OPTIONS_LIST = "upsert option cannot be an empty array, atleast one object of table and column is required"
    INVALID_UPSERT_TABLE_TYPE = "upsert object table key has value of type %s, expected string"
    INVALID_UPSERT_COLUMN_TYPE = "upsert object column key has value of type %s, expected string"
    EMPTY_UPSERT_OPTION_TABLE = "upsert object table value is empty string at index %s, expected non-empty string"
    EMPTY_UPSERT_OPTION_COLUMN = "upsert object column value is empty string at index %s, expected non-empty string"

class SkyflowError(Exception):
    def __init__(self, code, message="An Error occured", data={}, interface: str = 'Unknown') -> None:
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
