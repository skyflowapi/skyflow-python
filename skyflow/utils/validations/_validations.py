import json
import re
from skyflow.service_account import is_expired
from skyflow.utils.enums import LogLevel, TokenStrict, Env, RedactionType
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.utils.logger import log_info, log_error_log

valid_vault_config_keys = ["vault_id", "cluster_id", "credentials", "env"]
valid_connection_config_keys = ["connection_id", "connection_url", "credentials"]
valid_credentials_keys = ["path", "roles", "context", "token", "credentials_string"]
invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def validate_required_field(logger, config, field_name, expected_type, empty_error, invalid_error):
    field_value = config.get(field_name)

    if field_name not in config or not isinstance(field_value, expected_type):
        if field_name == "vault_id":
            logger.error(SkyflowMessages.ErrorLogs.VAULTID_IS_REQUIRED.value)
        if field_name == "cluster_id":
            logger.error(SkyflowMessages.ErrorLogs.CLUSTER_ID_IS_REQUIRED.value)
        if field_name == "connection_id":
            logger.error(SkyflowMessages.ErrorLogs.CONNECTION_ID_IS_REQUIRED.value)
        if field_name == "connection_url":
            logger.error(SkyflowMessages.ErrorLogs.INVALID_CONNECTION_URL.value)
        raise SkyflowError(invalid_error, invalid_input_error_code)

    if isinstance(field_value, str) and not field_value.strip():
        if field_name == "vault_id":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_VAULTID.value)
        if field_name == "cluster_id":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_CLUSTER_ID.value)
        if field_name == "connection_id":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_CONNECTION_ID.value)
        if field_name == "connection_url":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_CONNECTION_URL.value)
        if field_name == "path":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_CREDENTIALS_PATH.value)
        if field_name == "credentials_string":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_CREDENTIALS_STRING.value)
        if field_name == "token":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_TOKEN_VALUE.value)
        if field_name == "api_key":
            logger.error(SkyflowMessages.ErrorLogs.EMPTY_API_KEY_VALUE.value)
        raise SkyflowError(empty_error, invalid_input_error_code)

def validate_api_key(api_key: str, logger = None) -> bool:
    if len(api_key) != 42:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_API_KEY.value, logger = logger)
        return False
    api_key_pattern = re.compile(r'^sky-[a-zA-Z0-9]{5}-[a-fA-F0-9]{32}$')

    return bool(api_key_pattern.match(api_key))

def validate_credentials(logger, credentials, config_id_type=None, config_id=None):
    key_present = [k for k in ["path", "token", "credentials_string", "api_key"] if credentials.get(k)]

    if len(key_present) == 0:
        error_message = (
            SkyflowMessages.Error.INVALID_CREDENTIALS_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            SkyflowMessages.Error.INVALID_CREDENTIALS.value
        )
        raise SkyflowError(error_message, invalid_input_error_code)
    elif len(key_present) > 1:
        error_message = (
            SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED.value
        )
        raise SkyflowError(error_message, invalid_input_error_code)

    if "roles" in credentials:
        validate_required_field(
            logger, credentials, "roles", list,
            SkyflowMessages.Error.INVALID_ROLES_KEY_TYPE_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_ROLES_KEY_TYPE.value,
            SkyflowMessages.Error.EMPTY_ROLES_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_ROLES.value
        )

    if "context" in credentials:
        validate_required_field(
            logger, credentials, "context", str,
            SkyflowMessages.Error.EMPTY_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CONTEXT.value,
            SkyflowMessages.Error.INVALID_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CONTEXT.value
        )

    if "credentials_string" in credentials:
        validate_required_field(
            logger, credentials, "credentials_string", str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIALS_STRING.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value
        )
    elif "path" in credentials:
        validate_required_field(
            logger, credentials, "path", str,
            SkyflowMessages.Error.EMPTY_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIAL_FILE_PATH.value,
            SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value
        )
    elif "token" in credentials:
        validate_required_field(
            logger, credentials, "token", str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIALS_TOKEN.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value
        )
        if is_expired(credentials.get("token"), logger):
            raise SkyflowError(
                SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
                if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value,
                invalid_input_error_code
            )
    elif "api_key" in credentials:
        validate_required_field(
            logger, credentials, "api_key", str,
            SkyflowMessages.Error.EMPTY_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_API_KEY.value,
            SkyflowMessages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_API_KEY.value
        )
        if not validate_api_key(credentials.get("api_key"), logger):
            raise SkyflowError(SkyflowMessages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
                               if config_id_type and config_id else SkyflowMessages.Error.INVALID_API_KEY.value,
                               invalid_input_error_code)

def validate_log_level(logger, log_level):
    if not isinstance(log_level, LogLevel):
        raise SkyflowError( SkyflowMessages.Error.INVALID_LOG_LEVEL.value, invalid_input_error_code)

    if log_level is None:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_LOG_LEVEL.value, invalid_input_error_code)

def validate_keys(logger, config, config_keys):
    for key in config.keys():
        if key not in config_keys:
            raise SkyflowError(SkyflowMessages.Error.INVALID_KEY.value.format(key), invalid_input_error_code)

def validate_vault_config(logger, config):
    log_info(SkyflowMessages.Info.VALIDATING_VAULT_CONFIG.value, logger)
    validate_keys(logger, config, valid_vault_config_keys)

    # Validate vault_id (string, not empty)
    validate_required_field(
        logger, config, "vault_id", str,
        SkyflowMessages.Error.EMPTY_VAULT_ID.value,
        SkyflowMessages.Error.INVALID_VAULT_ID.value
    )
    vault_id = config.get("vault_id")
    # Validate cluster_id (string, not empty)
    validate_required_field(
        logger, config, "cluster_id", str,
        SkyflowMessages.Error.EMPTY_CLUSTER_ID.value.format(vault_id),
        SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id)
    )

    # Validate credentials (dict, not empty)
    if "credentials" in config and not config.get("credentials"):
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("vault", vault_id), invalid_input_error_code)

    if "credentials" in config and config.get("credentials"):
        validate_credentials(logger, config.get("credentials"), "vault", vault_id)

    # Validate env (optional, should be one of LogLevel values)
    if "env" in config and config.get("env") not in Env:
        logger.error(SkyflowMessages.ErrorLogs.VAULTID_IS_REQUIRED.value)
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    return True

def validate_update_vault_config(logger, config):

    validate_keys(logger, config, valid_vault_config_keys)

    # Validate vault_id (string, not empty)
    validate_required_field(
        logger, config, "vault_id", str,
        SkyflowMessages.Error.EMPTY_VAULT_ID.value,
        SkyflowMessages.Error.INVALID_VAULT_ID.value
    )

    vault_id = config.get("vault_id")

    if "cluster_id" in config and not config.get("cluster_id"):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id), invalid_input_error_code)

    if "env" in config and config.get("env") not in Env:
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("vault", vault_id), invalid_input_error_code)

    validate_credentials(logger, config.get("credentials"), "vault", vault_id)

    return True

def validate_connection_config(logger, config):
    log_info(SkyflowMessages.Info.VALIDATING_CONNECTION_CONFIG.value, logger)
    validate_keys(logger, config, valid_connection_config_keys)

    validate_required_field(
        logger, config, "connection_id" , str,
        SkyflowMessages.Error.EMPTY_CONNECTION_ID.value,
        SkyflowMessages.Error.INVALID_CONNECTION_ID.value
    )

    connection_id = config.get("connection_id")

    validate_required_field(
        logger, config, "connection_url", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_URL.value.format(connection_id),
        SkyflowMessages.Error.INVALID_CONNECTION_URL.value.format(connection_id)
    )

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("connection", connection_id), invalid_input_error_code)

    validate_credentials(logger, config.get("credentials"), "connection", connection_id)

    return True

def validate_update_connection_config(logger, config):

    validate_keys(logger, config, valid_connection_config_keys)

    validate_required_field(
        logger, config, "connection_id", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_ID.value,
        SkyflowMessages.Error.INVALID_CONNECTION_ID.value
    )

    connection_id = config.get("connection_id")

    validate_required_field(
        logger, config, "connection_url", str,
        SkyflowMessages.Error.EMPTY_CONNECTION_URL.value.format(connection_id),
        SkyflowMessages.Error.INVALID_CONNECTION_URL.value.format(connection_id)
    )

    if "credentials" not in config:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("connection", connection_id), invalid_input_error_code)
    validate_credentials(logger, config.get("credentials"))

    return True


def validate_insert_request(logger, request):
    if not isinstance(request.table_name, str):
        log_error_log(SkyflowMessages.ErrorLogs.TABLE_IS_REQUIRED.value.format("INSERT"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_NAME_IN_INSERT.value, invalid_input_error_code)
    if not request.table_name.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TABLE_NAME.value.format("INSERT"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_INSERT.value, invalid_input_error_code)

    if not isinstance(request.values, list) or not all(isinstance(v, dict) for v in request.values):
        log_error_log(SkyflowMessages.ErrorLogs.VALUES_IS_REQUIRED.value.format("INSERT"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code)

    if not len(request.values):
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_VALUES.value.format("INSERT"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_DATA_IN_INSERT.value, invalid_input_error_code)

    for i, item in enumerate(request.values, start=1):
        for key, value in item.items():
            if key is None or key == "":
                log_error_log(SkyflowMessages.ErrorLogs.EMPTY_OR_NULL_KEY_IN_VALUES.value.format("INSERT"), logger = logger)

            if value is None or value == "":
                log_error_log(SkyflowMessages.ErrorLogs.EMPTY_OR_NULL_VALUE_IN_VALUES.value.format("INSERT", key), logger = logger)

    if request.upsert is not None and (not isinstance(request.upsert, str) or not request.upsert.strip()):
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_UPSERT.value("INSERT"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_OPTIONS_TYPE.value, invalid_input_error_code)

    if request.homogeneous is not None and not isinstance(request.homogeneous, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_HOMOGENEOUS_TYPE.value, invalid_input_error_code)

    if request.upsert and request.homogeneous:
        log_error_log(SkyflowMessages.ErrorLogs.HOMOGENOUS_NOT_SUPPORTED_WITH_UPSERT.value.format("INSERT"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.HOMOGENOUS_NOT_SUPPORTED_WITH_UPSERT.value.format("INSERT"), invalid_input_error_code)

    if request.token_strict is not None:
        if not isinstance(request.token_strict, TokenStrict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_STRICT_TYPE.value, invalid_input_error_code)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code)

    if not isinstance(request.continue_on_error, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CONTINUE_ON_ERROR_TYPE.value, invalid_input_error_code)

    if request.tokens:
        for i, item in enumerate(request.tokens, start=1):
            for key, value in item.items():
                if key is None or key == "":
                    log_error_log(SkyflowMessages.ErrorLogs.EMPTY_OR_NULL_VALUE_IN_TOKENS.value.format("INSERT"),
                                  logger=logger)

                if value is None or value == "":
                    log_error_log(SkyflowMessages.ErrorLogs.EMPTY_OR_NULL_KEY_IN_TOKENS.value.format("INSERT", key),
                                  logger=logger)
        if not isinstance(request.tokens, list) or not request.tokens or not all(
                isinstance(t, dict) for t in request.tokens):
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TOKENS.value("INSERT"), logger = logger)
            raise SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code)

    if request.token_strict == TokenStrict.ENABLE and not request.tokens:
        raise SkyflowError(SkyflowMessages.Error.NO_TOKENS_IN_INSERT.value.format(request.token_strict), invalid_input_error_code)

    if request.token_strict == TokenStrict.DISABLE and request.tokens:
        raise SkyflowError(SkyflowMessages.Error.TOKENS_PASSED_FOR_TOKEN_STRICT_DISABLE.value, invalid_input_error_code)

    if request.token_strict == TokenStrict.ENABLE_STRICT:
        if len(request.values) != len(request.tokens):
            log_error_log(SkyflowMessages.ErrorLogs.INSUFFICIENT_TOKENS_PASSED_FOR_BYOT_ENABLE_STRICT.value.format("INSERT"), logger = logger)
            raise SkyflowError(SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value, invalid_input_error_code)

        for v, t in zip(request.values, request.tokens):
            if set(v.keys()) != set(t.keys()):
                log_error_log(SkyflowMessages.ErrorLogs.MISMATCH_OF_FIELDS_AND_TOKENS.value.format("INSERT"), logger=logger)
                raise SkyflowError(SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value, invalid_input_error_code)

def validate_delete_request(logger, request):
    if not isinstance(request.table, str):
        log_error_log(SkyflowMessages.ErrorLogs.TABLE_IS_REQUIRED.value.format("DELETE"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_VALUE.value, invalid_input_error_code)
    if not request.table.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TABLE_NAME.value.format("DELETE"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TABLE_VALUE.value, invalid_input_error_code)

    if not request.ids:
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_IDS.value.format("DELETE"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORD_IDS_IN_DELETE.value, invalid_input_error_code)

def validate_query_request(logger, request):
    if not request.query:
        log_error_log(SkyflowMessages.ErrorLogs.QUERY_IS_REQUIRED.value.format("QUERY"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_QUERY.value, invalid_input_error_code)

    if not isinstance(request.query, str):
        query_type = str(type(request.query))
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_TYPE.value.format(query_type), invalid_input_error_code)

    if not request.query.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_QUERY.value.format("QUERY"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_QUERY.value, invalid_input_error_code)

    if not request.query.upper().startswith("SELECT"):
        command = request.query
        raise  SkyflowError(SkyflowMessages.Error.INVALID_QUERY_COMMAND.value.format(command), invalid_input_error_code)

def validate_get_request(logger, request):
    redaction_type = request.redaction_type
    column_name = request.column_name
    column_values = request.column_values
    skyflow_ids = request.ids
    fields = request.fields
    offset = request.offset
    limit = request.limit
    download_url = request.download_url

    if not isinstance(request.table, str):
        log_error_log(SkyflowMessages.ErrorLogs.TABLE_IS_REQUIRED.value.format("GET"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_VALUE.value, invalid_input_error_code)
    if not request.table.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TABLE_NAME.value.format("GET"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TABLE_VALUE.value, invalid_input_error_code)

    if not skyflow_ids and not column_name and not column_values:
        log_error_log(SkyflowMessages.ErrorLogs.NEITHER_IDS_NOR_COLUMN_NAME_PASSED.value.format("GET"), logger = logger)

    if skyflow_ids and (not isinstance(skyflow_ids, list) or not skyflow_ids):
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_IDS.value.format("GET"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_IDS_TYPE.value.format(type(skyflow_ids)), invalid_input_error_code)

    if skyflow_ids:
        for index, skyflow_id in enumerate(skyflow_ids):
            if skyflow_id is None or skyflow_id == "":
                log_error_log(SkyflowMessages.ErrorLogs.EMPTY_OR_NULL_ID_IN_IDS.value.format("GET", index),
                              logger=logger)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code)

    if redaction_type is not None and not isinstance(redaction_type, RedactionType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(type(redaction_type)), invalid_input_error_code)

    if fields is not None and (not isinstance(fields, list) or not fields):
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_FIELDS.value.format("GET"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_FIELDS_VALUE.value.format(type(fields)), invalid_input_error_code)

    if offset is not None and limit is not None:
        raise SkyflowError(
            SkyflowMessages.Error.BOTH_OFFSET_AND_LIMIT_SPECIFIED.value,
            invalid_input_error_code)

    if offset is not None and not isinstance(offset, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_OFF_SET_VALUE.value(type(offset)), invalid_input_error_code)

    if limit is not None and not isinstance(limit, str):
        raise SkyflowError(SkyflowMessages.Error.INVALID_LIMIT_VALUE.value(type(limit)), invalid_input_error_code)

    if download_url is not None and not isinstance(download_url, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_DOWNLOAD_URL_VALUE.value(type(download_url)), invalid_input_error_code)

    if column_name is not None and (not isinstance(column_name, str) or not column_name.strip()):
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_NAME.value.format(type(column_name)), invalid_input_error_code)

    if column_values is not None and (
            not isinstance(column_values, list) or not column_values or not all(
            isinstance(val, str) for val in column_values)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_VALUE.value.format(type(column_values)), invalid_input_error_code)

    if request.return_tokens and redaction_type:
        log_error_log(SkyflowMessages.ErrorLogs.TOKENIZATION_NOT_SUPPORTED_WITH_REDACTION.value.format("GET"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.REDACTION_WITH_TOKENS_NOT_SUPPORTED.value, invalid_input_error_code)

    if (column_name or column_values) and request.return_tokens:
        log_error_log(SkyflowMessages.ErrorLogs.TOKENIZATION_SUPPORTED_ONLY_WITH_IDS.value.format("GET"),
                      logger=logger)
        raise SkyflowError(SkyflowMessages.Error.TOKENS_GET_COLUMN_NOT_SUPPORTED.value, invalid_input_error_code)

    if column_values and not column_name:
        log_error_log(SkyflowMessages.ErrorLogs.COLUMN_VALUES_IS_REQUIRED_GET.value.format("GET"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_VALUE.value.format(type(column_values)), invalid_input_error_code)

    if column_name and not column_values:
        log_error_log(SkyflowMessages.ErrorLogs.COLUMN_NAME_IS_REQUIRED.value.format("GET"), logger = logger)
        SkyflowError(SkyflowMessages.Error.INVALID_COLUMN_NAME.value.format(type(column_name)), invalid_input_error_code)

    if (column_name or column_values) and skyflow_ids:
        log_error_log(SkyflowMessages.ErrorLogs.BOTH_IDS_AND_COLUMN_NAME_PASSED.value.format("GET"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.BOTH_IDS_AND_COLUMN_DETAILS_SPECIFIED.value, invalid_input_error_code)

def validate_update_request(logger, request):
    skyflow_id = ""
    field = {key: value for key, value in request.data.items() if key != "skyflow_id"}

    try:
        skyflow_id = request.data.get("skyflow_id")
    except Exception:
        log_error_log(SkyflowMessages.ErrorLogs.SKYFLOW_ID_IS_REQUIRED.value.format("UPDATE"), logger=logger)

    if not skyflow_id.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_SKYFLOW_ID.value.format("UPDATE"), logger = logger)

    if not isinstance(request.table, str):
        log_error_log(SkyflowMessages.ErrorLogs.TABLE_IS_REQUIRED.value.format("UPDATE"), logger=logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_VALUE.value, invalid_input_error_code)
    if not request.table.strip():
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TABLE_NAME.value.format("UPDATE"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TABLE_VALUE.value, invalid_input_error_code)

    if not isinstance(request.return_tokens, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RETURN_TOKENS_TYPE.value, invalid_input_error_code)

    if not isinstance(request.data, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_FIELDS_TYPE.value(type(request.data)), invalid_input_error_code)

    if not len(request.data.items()):
        raise SkyflowError(SkyflowMessages.Error.UPDATE_FIELD_KEY_ERROR.value, invalid_input_error_code)

    if request.token_strict is not None:
        if not isinstance(request.token_strict, TokenStrict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_STRICT_TYPE.value, invalid_input_error_code)

    if request.tokens:
        if not isinstance(request.tokens, dict) or not request.tokens:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TOKENS.value.format("UPDATE"), logger=logger)
            raise SkyflowError(SkyflowMessages.Error.INVALID_TYPE_OF_DATA_IN_INSERT.value, invalid_input_error_code)

    if request.token_strict == TokenStrict.ENABLE and not request.tokens:
        raise SkyflowError(SkyflowMessages.Error.NO_TOKENS_IN_INSERT.value.format(request.token_Strict),
                           invalid_input_error_code)

    if request.token_strict == TokenStrict.DISABLE and request.tokens:
        raise SkyflowError(SkyflowMessages.Error.TOKENS_PASSED_FOR_TOKEN_STRICT_DISABLE.value, invalid_input_error_code)

    if request.token_strict == TokenStrict.ENABLE_STRICT:
        if len(field) != len(request.tokens):
            log_error_log(
                SkyflowMessages.ErrorLogs.INSUFFICIENT_TOKENS_PASSED_FOR_BYOT_ENABLE_STRICT.value.format("UPDATE"),
                logger=logger)
            raise SkyflowError(SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value,
                               invalid_input_error_code)

        if set(field.keys()) != set(request.tokens.keys()):
            log_error_log(
                SkyflowMessages.ErrorLogs.INSUFFICIENT_TOKENS_PASSED_FOR_BYOT_ENABLE_STRICT.value.format("UPDATE"),
                logger=logger)
            raise SkyflowError(
                SkyflowMessages.Error.INSUFFICIENT_TOKENS_PASSED_FOR_TOKEN_STRICT_ENABLE_STRICT.value,
                invalid_input_error_code)

def validate_detokenize_request(logger, request):
    if not isinstance(request.redaction_type, RedactionType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(type(request.redaction_type)), invalid_input_error_code)

    if not isinstance(request.continue_on_error, bool):
        raise SkyflowError(SkyflowMessages.Error.INVALID_CONTINUE_ON_ERROR_TYPE.value, invalid_input_error_code)

    if not len(request.tokens):
        log_error_log(SkyflowMessages.ErrorLogs.TOKENS_REQUIRED.value.format("DETOKENIZE"), logger = logger)
        log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TOKENS.value.format("DETOKENIZE"), logger = logger)
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENS_LIST_VALUE.value, invalid_input_error_code)

    if not isinstance(request.tokens, list):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENS_LIST_VALUE.value(type(request.tokens)), invalid_input_error_code)

def validate_tokenize_request(logger, request):
    parameters = request.tokenize_parameters
    if not isinstance(parameters, list):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETERS.value.format(type(parameters)), invalid_input_error_code)

    if not len(parameters):
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETERS.value, invalid_input_error_code)

    for i, param in enumerate(parameters):
        if not isinstance(param, dict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETER.value.format(i, type(param)), invalid_input_error_code)

        allowed_keys = {"value", "column_group"}

        if set(param.keys()) != allowed_keys:
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETER_KEY.value.format(i), invalid_input_error_code)

        if not param.get("value"):
            log_error_log(SkyflowMessages.ErrorLogs.COLUMN_VALUES_IS_REQUIRED_TOKENIZE.value.format("TOKENIZE"), logger = logger)
            raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETER_VALUE.value.format(i), invalid_input_error_code)
        if not param.get("column_group"):
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_COLUMN_GROUP_IN_COLUMN_VALUES.value.format("TOKENIZE"), logger = logger)
            raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETER_COLUMN_GROUP.value.format(i), invalid_input_error_code)

def validate_invoke_connection_params(logger, query_params, path_params):
    if not isinstance(path_params, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_PATH_PARAMS.value, invalid_input_error_code)

    if not isinstance(query_params, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code)

    for param, value in path_params.items():
        if not(isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_PATH_PARAMS.value, invalid_input_error_code)

    for param, value in query_params.items():
        if not isinstance(param, str):
            raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code)

    try:
        json.dumps(query_params)
    except TypeError:
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_PARAMS.value, invalid_input_error_code)
