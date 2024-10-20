import json

from skyflow.service_account import is_expired
from skyflow.utils.enums import LogLevel, TokenStrict, Redaction, Env
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages, log_error

valid_vault_config_keys = ["vault_id", "cluster_id", "credentials", "env"]
valid_connection_config_keys = ["connection_id", "connection_url", "credentials"]
valid_credentials_keys = ["path", "roles", "context", "token", "credentials_string"]
invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def validate_required_field(logger, config, field_name, expected_type, empty_error, invalid_error):
    field_value = config.get(field_name)

    if field_name not in config or not isinstance(field_value, expected_type):
        raise SkyflowError(invalid_error, invalid_input_error_code, logger = logger, logger_method=log_error)

    if isinstance(field_value, str) and not field_value.strip():
        raise SkyflowError(empty_error, invalid_input_error_code, logger = logger, logger_method=log_error)

def validate_credentials(logger, credentials):
    key_present = [k for k in ["path", "token", "credentials_string", "api_key"] if credentials.get(k)]
    if len(key_present) == 0:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    elif len(key_present) > 1:
        raise SkyflowError(SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if "roles" in credentials:
        validate_required_field(
            logger, credentials, "roles", list,
            SkyflowMessages.Error.INVALID_ROLES_KEY_TYPE.value,
            SkyflowMessages.Error.EMPTY_ROLES.value
        )

    if "context" in credentials:
        validate_required_field(
            logger, credentials, "context", str,
            SkyflowMessages.Error.EMPTY_CONTEXT.value,
            SkyflowMessages.Error.INVALID_CONTEXT.value
        )

    if "credentials_string" in credentials:
        validate_required_field(
            logger, credentials, "credentials_string", str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_STRING.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value
        )
    elif "path" in credentials:
        validate_required_field(
            logger, credentials, "path", str,
            SkyflowMessages.Error.EMPTY_CREDENTIAL_FILE_PATH.value,
            SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value
        )
    elif "token" in credentials:
        validate_required_field(
            logger, credentials, "token", str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_TOKEN.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value
        )

        if is_expired(credentials.get("token"), logger):
            raise SkyflowError()
    elif "api_key" in credentials:
        validate_required_field(
            logger, credentials, "api_key", str,
            SkyflowMessages.Error.EMPTY_API_KEY.value,
            SkyflowMessages.Error.INVALID_API_KEY.value
        )

def validate_log_level(logger, log_level):
    if not isinstance(log_level, LogLevel):
        raise SkyflowError( SkyflowMessages.Error.INVALID_LOG_LEVEL.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if log_level is None:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_LOG_LEVEL.value, invalid_input_error_code, logger = logger, logger_method=log_error)

def validate_keys(logger, config, config_keys):
    for key in config.keys():
        if key not in config_keys:
            raise SkyflowError(SkyflowMessages.Error.INVALID_KEY.value.format(key), invalid_input_error_code, logger = logger, logger_method=log_error)

def validate_vault_config(logger, config):

    validate_keys(logger, config, valid_vault_config_keys)

    # Validate vault_id (string, not empty)
    validate_required_field(
        logger, config, "vault_id", str,
        SkyflowMessages.Error.EMPTY_VAULT_ID.value,
        SkyflowMessages.Error.INVALID_VAULT_ID.value
    )

    # Validate cluster_id (string, not empty)
    validate_required_field(
        logger, config, "cluster_id", str,
        SkyflowMessages.Error.EMPTY_CLUSTER_ID.value,
        SkyflowMessages.Error.INVALID_CLUSTER_ID.value
    )

    # Validate credentials (dict, not empty)
    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    validate_credentials(logger, config.get("credentials"))

    # Validate env (optional, should be one of LogLevel values)
    if "env" in config and config.get("env") not in Env:
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    return True

def validate_update_vault_config(logger, config):

    validate_keys(logger, config, valid_vault_config_keys)

    # Validate vault_id (string, not empty)
    validate_required_field(
        logger, config, "vault_id", str,
        SkyflowMessages.Error.EMPTY_VAULT_ID.value,
        SkyflowMessages.Error.INVALID_VAULT_ID.value
    )

    if "cluster_id" in config and not config.get("cluster_id"):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CLUSTER_ID.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if "env" in config and config.get("env") not in LogLevel:
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    validate_credentials(logger, config.get("credentials"))

    return True

def validate_connection_config(logger, config):
    validate_keys(logger, config, valid_connection_config_keys)

    validate_required_field(
        logger, config, "connection_id" , str,
        SkyflowMessages.Error.EMPTY_CONNECTION_ID.value,
        SkyflowMessages.Error.INVALID_CONNECTION_ID.value
    )

    validate_required_field(
        logger, config, "connection_url", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_URL.value,
        SkyflowMessages.Error.INVALID_CONNECTION_URL.value
    )

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    validate_credentials(logger, config.get("credentials"))

    return True

def validate_update_connection_config(logger, config):

    validate_keys(logger, config, valid_connection_config_keys)

    validate_required_field(
        logger, config, "connection_id", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_ID.value,
        SkyflowMessages.Error.INVALID_CONNECTION_ID.value
    )

    validate_required_field(
        logger, config, "connection_url", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_URL.value,
        SkyflowMessages.Error.INVALID_CONNECTION_URL.value
    )

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS, invalid_input_error_code, logger = logger, logger_method=log_error)
    validate_credentials(logger, config.get("credentials"))

    return True


def validate_insert_request(logger, request):
    if not isinstance(request.table_name, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_NAME_IN_INSERT.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    if not request.table_name.strip():
        raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_INSERT.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.values, list) or not all(isinstance(v, dict) for v in request.values):
        raise  SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not len(request.values):
        raise SkyflowError(SkyflowMessages.Error.EMPTY_DATA_IN_INSERT.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.upsert is not None and (not isinstance(request.upsert, str) or not request.upsert.strip()):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_OPTIONS_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.homogeneous, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_HOMOGENEOUS_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.token_strict is not None:
        if not isinstance(request.token_strict, TokenStrict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_STRICT_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.continue_on_error, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CONTINUE_ON_ERROR_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.tokens:
        if not isinstance(request.tokens, list) or not request.tokens or not all(
                isinstance(t, dict) for t in request.tokens):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code,
                               logger=logger, logger_method=log_error)

    if request.token_strict == TokenStrict.ENABLE and not request.tokens:
        raise SkyflowError(SkyflowMessages.Error.NO_TOKENS_IN_INSERT.value.format(request.token_Strict), invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.token_strict == TokenStrict.DISABLE and request.tokens:
        raise SkyflowError(SkyflowMessages.Error.TOKENS_PASSED_FOR_TOKEN_STRICT_DISABLE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.token_strict == TokenStrict.ENABLE_STRICT:
        if len(request.values) != len(request.tokens):
            raise SkyflowError(SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value, invalid_input_error_code, logger = logger, logger_method=log_error)

        for v, t in zip(request.values, request.tokens):
            if set(v.keys()) != set(t.keys()):
                raise SkyflowError(SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value, invalid_input_error_code, logger = logger, logger_method=log_error)


def validate_delete_request(logger, request):
    if not isinstance(request.table, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_VALUE.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    if not request.table.strip():
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TABLE_VALUE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not request.ids:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORD_IDS_IN_DELETE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

def validate_query_request(logger, request):
    if not isinstance(request.query, str):
        query_type = str(type(request.query))
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_TYPE.value.format(query_type), invalid_input_error_code, logger = logger, logger_method=log_error)

    if not request.query.strip():
        raise SkyflowError(SkyflowMessages.Error.EMPTY_QUERY.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not request.query.upper().startswith("SELECT"):
        command = request.query
        raise  SkyflowError(SkyflowMessages.Error.INVALID_QUERY_COMMAND.value.format(command), invalid_input_error_code, logger = logger, logger_method=log_error)

def validate_get_request(logger, request):
    redaction_type = request.redaction_type
    column_name = request.column_name
    column_values = request.column_values
    skyflow_ids = request.ids
    fields = request.fields
    offset = request.offset
    limit = request.limit
    download_url = request.download_url

    if skyflow_ids and (not isinstance(skyflow_ids, list) or not skyflow_ids):
        raise SkyflowError(SkyflowMessages.Error.INVALID_IDS_TYPE.value.format(type(skyflow_ids)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if redaction_type is not None and not isinstance(redaction_type, Redaction):
        raise SkyflowError(SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(type(redaction_type)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if fields is not None and (not isinstance(fields, list) or not fields):
        raise SkyflowError(SkyflowMessages.Error.INVALID_FIELDS_VALUE.value.format(type(fields)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if offset is not None and limit is not None:
        raise SkyflowError(
            SkyflowMessages.Error.BOTH_OFFSET_AND_LIMIT_SPECIFIED.value,
            invalid_input_error_code, logger=logger, logger_method=log_error)

    if offset is not None and not isinstance(offset, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_OFF_SET_VALUE.value(type(offset)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if limit is not None and not isinstance(limit, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_LIMIT_VALUE.value(type(limit)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if download_url is not None and not isinstance(download_url, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_DOWNLOAD_URL_VALUE.value(type(download_url)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if column_name is not None and (not isinstance(column_name, str) or not column_name.strip()):
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_NAME.value.format(type(column_name)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if column_values is not None and (
            not isinstance(column_values, list) or not column_values or not all(
            isinstance(val, str) for val in column_values)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_VALUE.value.format(type(column_values)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.return_tokens and redaction_type:
        raise SkyflowError(SkyflowMessages.Error.REDACTION_WITH_TOKENS_NOT_SUPPORTED.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if (column_name or column_values) and request.return_tokens:
        raise SkyflowError(SkyflowMessages.Error.TOKENS_GET_COLUMN_NOT_SUPPORTED.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if column_values and not column_name:
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_VALUE.value.format(type(column_values)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if column_name and not column_values:
        SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_NAME.value.format(type(column_name)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if (column_name or column_values) and skyflow_ids:
        raise SkyflowError(SkyflowMessages.Error.BOTH_IDS_AND_COLUMN_DETAILS_SPECIFIED.value, invalid_input_error_code, logger = logger, logger_method=log_error)





def validate_update_request(logger, request):
    if not isinstance(request.table, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_VALUE.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    if not request.table.strip():
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TABLE_VALUE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.data, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_FIELDS_TYPE.value(type(request.data)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if not len(request.data.items()):
        raise SkyflowError(SkyflowMessages.Error.UPDATE_FIELD_KEY_ERROR.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.token_strict is not None:
        if not isinstance(request.token_strict, TokenStrict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_STRICT_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if request.tokens:
        if not isinstance(request.tokens, list) or not request.tokens or not all(
                isinstance(t, dict) for t in request.tokens):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code,
                               logger=logger, logger_method=log_error)

    if 'id' not in request.data:
        raise SkyflowError(SkyflowMessages.Error.IDS_KEY_ERROR.value, invalid_input_error_code, logger = logger, logger_method=log_error)


def validate_detokenize_request(logger, request):
    if not isinstance(request.redaction_type, Redaction):
        raise SkyflowError(SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(type(request.redaction_type)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.continue_on_error, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CONTINUE_ON_ERROR_TYPE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not len(request.tokens):
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENS_LIST_VALUE.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(request.tokens, list):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENS_LIST_VALUE.value(type(request.tokens)), invalid_input_error_code, logger = logger, logger_method=log_error)


def validate_tokenize_request(logger, request):
    parameters = request.tokenize_parameters
    if not isinstance(parameters, list):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETERS.value.format(type(parameters)), invalid_input_error_code, logger = logger, logger_method=log_error)

    if not len(parameters):
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETERS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    for i, param in enumerate(parameters):
        if not isinstance(param, dict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETER.value.format(i, type(param)), invalid_input_error_code, logger = logger, logger_method=log_error)

        allowed_keys = {"value", "column_group"}

        if set(param.keys()) != allowed_keys:
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETER_KEY.value.format(i), invalid_input_error_code, logger = logger, logger_method=log_error)

        if not param.get("value"):
            raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETER_VALUE.value.format(i), invalid_input_error_code, logger = logger, logger_method=log_error)
        if not param.get("column_group"):
            raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETER_COLUMN_GROUP.value.format(i), invalid_input_error_code, logger = logger, logger_method=log_error)


def validate_invoke_connection_params(logger, query_params, path_params):
    if not isinstance(path_params, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_PATH_PARAMS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not isinstance(query_params, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    for param, value in path_params.items():
        if not(isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_PATH_PARAMS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    for param, value in query_params.items():
        if not isinstance(param, str):
            raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    try:
        json.dumps(query_params)
    except TypeError:
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code, logger = logger, logger_method=log_error)
