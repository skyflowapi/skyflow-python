from enum import Enum

from ._version import SDK_VERSION

error_prefix = f"Skyflow Node SDK {SDK_VERSION}"

class SkyflowMessages:
    class ErrorCodes(Enum):
        INVALID_INPUT = 400
        INVALID_INDEX = 404
        SERVER_ERROR = 500
        PARTIAL_SUCCESS = 500
        TOKENS_GET_COLUMN_NOT_SUPPORTED = 400
        REDACTION_WITH_TOKENS_NOT_SUPPORTED = 400

    class Error(Enum):
        EMPTY_VAULT_ID = f"{error_prefix} Initialization failed. Invalid vault Id. Specify a valid vault Id."
        INVALID_VAULT_ID = f"{error_prefix} Initialization failed. Invalid vault Id. Specify a valid vault Id as a string."
        EMPTY_CLUSTER_ID = f"{error_prefix} Initialization failed. Invalid cluster Id. Specify a valid cluster Id."
        INVALID_CLUSTER_ID = f"{error_prefix} Initialization failed. Invalid cluster Id. Specify cluster Id as a string."
        INVALID_ENV = f"{error_prefix} Initialization failed. Invalid env. Specify a valid env."
        INVALID_KEY = f"{error_prefix} Initialization failed. Invalid {{}}. Specify a valid key"
        VAULT_ID_NOT_IN_CONFIG_LIST = f"{error_prefix} Validation error. {{}} is missing from the config. Specify the vaultId's from config."

        EMPTY_CREDENTIALS = f"{error_prefix} Validation error. Invalid credentials. Credentials must not be empty."
        INVALID_CREDENTIALS = f"{error_prefix} Validation error. Invalid credentials. Specify a valid credentials."
        MULTIPLE_CREDENTIALS_PASSED = f"{error_prefix} Validation error. Multiple credentials provided. Please specify only one valid credential."
        EMPTY_CREDENTIALS_STRING = f"{error_prefix} Validation error. Invalid credentials. Specify valid credentials."
        INVALID_CREDENTIALS_STRING = f"{error_prefix} Validation error. Invalid credentials. Specify credentials as a string."
        EMPTY_CREDENTIAL_FILE_PATH = f"{error_prefix} Initialization failed. Invalid credentials. Specify a valid file path."
        INVALID_CREDENTIAL_FILE_PATH = f"{error_prefix} Initialization failed. Invalid credentials. Expected file path to be a string."
        EMPTY_CREDENTIALS_TOKEN = f"{error_prefix} Initialization failed. Specify a valid credentials token."
        INVALID_CREDENTIALS_TOKEN = f"{error_prefix} Initialization failed. Invalid credentials token. Expected token to be a string."
        EXPIRED_TOKEN = f"${error_prefix} Initialization failed. Given token is expired. Specify a valid credentials token."
        EMPTY_API_KEY = f"{error_prefix} Initialization failed. Specify a valid api key."
        INVALID_API_KEY = f"{error_prefix} Initialization failed. Invalid api key. Expected api key to be a string."
        INVALID_ROLES_KEY_TYPE = f"{error_prefix} Validation error. Invalid roles. Specify roles as an array."
        EMPTY_ROLES = f"{error_prefix} Validation error. Invalid roles. Specify at least one role."
        EMPTY_CONTEXT = f"{error_prefix} Initialization failed. Invalid context provided. Specify context as type Context."
        INVALID_CONTEXT = f"{error_prefix} Initialization failed. Invalid context. Specify a valid context."
        INVALID_LOG_LEVEL = f"{error_prefix} Initialization failed. Invalid log level. Specify a valid log level."
        EMPTY_LOG_LEVEL = f"{error_prefix} Initialization failed. Specify a valid log level."

        EMPTY_CONNECTION_ID = f"{error_prefix} Initialization failed. Invalid connection Id. Specify a valid connection Id."
        INVALID_CONNECTION_ID = f"{error_prefix} Initialization failed. Invalid connection Id. Specify connection Id as a string."
        EMPTY_CONNECTION_URL = f"{error_prefix} Initialization failed. Invalid connection Url. Specify a valid connection Url."
        INVALID_CONNECTION_URL = f"{error_prefix} Initialization failed. Invalid connection Url. Specify connection Url as a string."
        CONNECTION_ID_NOT_IN_CONFIG_LIST = f"{error_prefix} Validation error. {{}} is missing from the config. Specify the connectionIds from config."

        MISSING_TABLE_NAME_IN_INSERT = f"{error_prefix} Validation error. Table name cannot be empty in insert request. Specify a table name."
        INVALID_TABLE_NAME_IN_INSERT = f"{error_prefix} Validation error. Invalid table name in insert request. Specify a valid table name."
        INVALID_TYPE_OF_DATA_IN_INSERT = f"{error_prefix} Validation error. Invalid type of data in insert request. Specify data as a object array."
        EMPTY_DATA_IN_INSERT = f"{error_prefix} Validation error. Data array cannot be empty. Specify data in insert request."
        INVALID_UPSERT_OPTIONS_TYPE = f"{error_prefix} Validation error. 'upsert' key cannot be empty in options. At least one object of table and column is required."
        INVALID_HOMOGENEOUS_TYPE = f"{error_prefix} Validation error. Invalid type of homogeneous. Specify homogeneous as a string."
        INVALID_TOKEN_STRICT_TYPE = f"{error_prefix} Validation error. Invalid type of token strict. Specify token strict as a enum."
        INVALID_RETURN_TOKENS_TYPE = f"{error_prefix} Validation error. Invalid type  of return tokens. Specify return tokens as a boolean."
        INVALID_CONTINUE_ON_ERROR_TYPE = f"{error_prefix} Validation error. Invalid type of continue on error. Specify continue on error as a boolean."
        TOKENS_PASSED_FOR_TOKEN_STRICT_DISABLE = f"{error_prefix} Validation error. 'token_strict' wasn't specified. Set 'token_strict' to 'ENABLE' to insert tokens."
        INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT = f"{error_prefix} Validation error. 'byot' is set to 'ENABLE_STRICT', but some fields are missing tokens. Specify tokens for all fields."
        NO_TOKENS_IN_INSERT = f"{error_prefix} Validation error. Tokens weren't specified for records while 'token_Strict' was {{}}. Specify tokens."
        BATCH_INSERT_FAILURE = f"{error_prefix} Insert operation failed."
        GET_FAILURE = f"{error_prefix} Get operation failed."

        EMPTY_TABLE_VALUE = f"{error_prefix} Validation error. 'table' can't be empty. Specify a table."
        INVALID_TABLE_VALUE = f"{error_prefix} Validation error. Invalid type of table. Specify table as a string"
        EMPTY_RECORD_IDS_IN_DELETE = f"{error_prefix} Validation error. 'record ids' array can't be empty. Specify one or more record ids."
        BULK_DELETE_FAILURE = f"{error_prefix} Delete operation failed."

        INVALID_QUERY_TYPE = f"{error_prefix} Validation error. Query parameter is of type {{}}. Specify as a string."
        EMPTY_QUERY = f"{error_prefix} Validation error. Query parameter can't be empty. Specify as a string."
        INVALID_QUERY_COMMAND = f"{error_prefix} Validation error. {{}} command was passed instead, but only SELECT commands are supported. Specify the SELECT command."
        SERVER_ERROR = f"{error_prefix} Validation error. Check SkyflowError.data for details."
        QUERY_FAILED = f"{error_prefix} Query operation failed."
        DETOKENIZE_FIELD = f"{error_prefix} Detokenize operation failed."
        UPDATE_FAILED = f"{error_prefix} Update operation failed."
        TOKENIZE_FAILED = f"{error_prefix} Tokenize operation failed."
        INVOKE_CONNECTION_FAILED = f"{error_prefix} Invoke Connection operation failed."

        INVALID_IDS_TYPE = f"{error_prefix} Validation error. 'ids' has a value of type {{}}. Specify 'ids' as list."
        INVALID_REDACTION_TYPE = f"{error_prefix} Validation error. 'redaction' has a value of type {{}}. Specify 'redaction' as type Skyflow.Redaction."
        INVALID_COLUMN_NAME = f"{error_prefix} Validation error. 'column' has a value of type {{}}. Specify 'column' as a string."
        INVALID_COLUMN_VALUE = f"{error_prefix} Validation error. columnValues key has a value of type {{}}. Specify columnValues key as list."
        INVALID_FIELDS_VALUE = f"{error_prefix} Validation error. fields key has a value of type{{}}. Specify fields key as list."
        BOTH_OFFSET_AND_LIMIT_SPECIFIED = f"${error_prefix} Validation error. Both offset and limit cannot be present at the same time"
        INVALID_OFF_SET_VALUE = f"{error_prefix} Validation error. offset key has a value of type {{}}. Specify offset key as integer."
        INVALID_LIMIT_VALUE = f"{error_prefix} Validation error. limit key has a value of type {{}}. Specify limit key as integer."
        INVALID_DOWNLOAD_URL_VALUE = f"{error_prefix} Validation error. download_url key has a value of type {{}}. Specify download_url key as boolean."
        REDACTION_WITH_TOKENS_NOT_SUPPORTED = f"{error_prefix} Validation error. 'redaction' can't be used when tokens are specified. Remove 'redaction' from payload if tokens are specified."
        TOKENS_GET_COLUMN_NOT_SUPPORTED = f"{error_prefix} Validation error. Column name and/or column values can't be used when tokens are specified. Remove unique column values or tokens from the payload."
        BOTH_IDS_AND_COLUMN_DETAILS_SPECIFIED = f"{error_prefix} Validation error. Both Skyflow IDs and column details can't be specified. Either specify Skyflow IDs or unique column details."
        INVALID_ORDER_BY_VALUE = f"{error_prefix} Validation error. order_by key has a value of type {{}}. Specify order_by key as Skyflow.OrderBy"

        UPDATE_FIELD_KEY_ERROR = f"{error_prefix} Validation error. Fields are empty in an update payload. Specify at least one field."
        INVALID_FIELDS_TYPE = f"{error_prefix} Validation error. The 'data' key has a value of type {{}}. Specify 'data' as a dictionary."
        IDS_KEY_ERROR = f"{error_prefix} Validation error. 'ids' key is missing from the payload. Specify an 'ids' key."
        INVALID_TOKENS_LIST_VALUE = f"{error_prefix} Validation error. The 'tokens' key has a value of type {{}}. Specify 'tokens' as a list."
        EMPTY_TOKENS_LIST_VALUE = f"{error_prefix} Validation error. Tokens are empty in detokenize payload. Specify at lease one token"

        INVALID_TOKENIZE_PARAMETERS = f"{error_prefix} Validation error. The 'tokenize_parameters' key has a value of type {{}}. Specify 'tokenize_parameters' as a list."
        EMPTY_TOKENIZE_PARAMETERS = f"{error_prefix} Validation error. Tokenize parameters are empty in tokenize payload. Specify at least one parameter."
        INVALID_TOKENIZE_PARAMETER = f"{error_prefix} Validation error. Tokenize parameter at index {{}} has a value of type {{}}. Specify as a dictionary."
        EMPTY_TOKENIZE_PARAMETER_VALUE = f"{error_prefix} Validation error. Tokenize parameter value at index {{}} is empty. Specify a valid value."
        EMPTY_TOKENIZE_PARAMETER_COLUMN_GROUP = f"{error_prefix} Validation error. Tokenize parameter column group at index {{}} is empty. Specify a valid column group."
        INVALID_TOKENIZE_PARAMETER_KEY = f"{error_prefix} Validation error. Tokenize parameter key at index {{}} is invalid. Specify a valid key value."

        INVALID_REQUEST_BODY = f"{error_prefix} Validation error. Invalid request body. Specify the request body as an object."
        INVALID_REQUEST_HEADERS = f"{error_prefix} Validation error. Invalid request headers. Specify the request as an object."
        INVALID_URL = f"{error_prefix} Validation error. Connection url {{}} is invalid. Specify a valid connection url."
        INVALID_PATH_PARAMS = f"{error_prefix} Validation error. Path parameters aren't valid. Specify valid path parameters."
        INVALID_QUERY_PARAMS = f"{error_prefix} Validation error. Query parameters aren't valid. Specify valid query parameters."

        MISSING_PRIVATE_KEY = f"{error_prefix} Initialization failed. Unable to read private key in credentials. Verify your private key."
        MISSING_CLIENT_ID = f"{error_prefix} Initialization failed. Unable to read client ID in credentials. Verify your client ID."
        MISSING_KEY_ID = f"{error_prefix} Initialization failed. Unable to read key ID in credentials. Verify your key ID."
        MISSING_TOKEN_URI = f"{error_prefix} Initialization failed. Unable to read token URI in credentials. Verify your token URI."
        JWT_INVALID_FORMAT = f"{error_prefix} Initialization failed. Invalid private key format. Verify your credentials."
        JWT_DECODE_ERROR = f"{error_prefix} Validation error. Invalid access token. Verify your credentials."
        FILE_INVALID_JSON = f"{error_prefix} Initialization failed. File at {{}} is not in valid JSON format. Verify the file contents."

    class Info(Enum):
        INITIALIZE_CLIENT = "Initializing skyflow client"
        CLIENT_INITIALIZED = "Initialized skyflow client successfully"
        VALIDATE_INSERT_RECORDS = "Validating insert records"
        VALIDATE_DELETE_RECORDS = "Validating delete records"
        VALIDATE_DETOKENIZE_INPUT = "Validating detokenize input"
        VALIDATE_GET_RECORDS = "Validating get records"
        VALIDATE_CONNECTION_CONFIG = "Validating connection config"
        INSERT_DATA_SUCCESS = "Data has been inserted successfully."
        DETOKENIZE_SUCCESS = "Data has been detokenized successfully."
        GET_SUCCESS = "Records fetched successfully."
        QUERY_SUCCESS = "Query executed successfully."
        BEARER_TOKEN_RECEIVED = "tokenProvider returned token successfully."
        INSERT_TRIGGERED = "Insert method triggered."
        DETOKENIZE_TRIGGERED = "Detokenize method triggered."
        GET_TRIGGERED = "Get triggered."
        INVOKE_CONNECTION_TRIGGERED = "Invoke connection triggered."
        QUERY_TRIGGERED = "Query method triggered."
        GENERATE_BEARER_TOKEN_TRIGGERED = "Generate bearer token triggered"
        GENERATE_BEARER_TOKEN_SUCCESS = "Generate bearer token returned successfully"
        IS_TOKEN_VALID_TRIGGERED = "isTokenValid() triggered"
        IS_EXPIRED_TRIGGERED = "is_expired() triggered"
        EMPTY_ACCESS_TOKEN = "Give access token is empty"
        INVALID_TOKEN = "Given token is invalid"
        UPDATE_TRIGGERED = "Update method triggered"
        UPDATE_DATA_SUCCESS = "Data has been updated successfully"
        DELETE_TRIGGERED = "Delete triggered."
        DELETE_DATA_SUCCESS = "Data has been deleted successfully."

    class Warning(Enum):
        WARNING_MESSAGE = "WARNING MESSAGE"

    class InterfaceName(Enum):
        CLIENT = "client"
        INSERT = "client.insert"
        DETOKENIZE = "client.detokenize"
        TOKENIZE = "client.tokenize"
        GET = "client.get"
        UPDATE = "client.update"
        INVOKE_CONNECTION = "client.invoke_connection"
        QUERY = "client.query"
        GENERATE_BEARER_TOKEN = "service_account.generate_bearer_token"
        IS_TOKEN_VALID = "service_account.is_token_valid"
        IS_EXPIRED = "service_account.is_expired"
        DELETE = "client.delete"


