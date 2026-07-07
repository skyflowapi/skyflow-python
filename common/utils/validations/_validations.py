from common.errors import SkyflowError
from common.service_account import is_expired
from common.utils import SkyflowMessages
from common.utils.constants import ApiKey, ConfigField, CredentialField, OptionField
from common.utils.enums import LogLevel
from common.utils.logger import log_error_log
from common.utils._helpers import is_valid_url

invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value


def validate_required_field(logger, config, field_name, expected_type, empty_error, invalid_error):
    field_value = config.get(field_name)

    if field_name not in config or not isinstance(field_value, expected_type):
        if field_name == ConfigField.VAULT_ID:
            log_error_log(SkyflowMessages.ErrorLogs.VAULTID_IS_REQUIRED.value, logger)
        if field_name == ConfigField.CLUSTER_ID:
            log_error_log(SkyflowMessages.ErrorLogs.CLUSTER_ID_IS_REQUIRED.value, logger)
        if field_name == OptionField.CONNECTION_ID:
            log_error_log(SkyflowMessages.ErrorLogs.CONNECTION_ID_IS_REQUIRED.value, logger)
        if field_name == OptionField.CONNECTION_URL:
            log_error_log(SkyflowMessages.ErrorLogs.INVALID_CONNECTION_URL.value, logger)
        raise SkyflowError(invalid_error, invalid_input_error_code)

    if isinstance(field_value, str) and not field_value.strip():
        if field_name == ConfigField.VAULT_ID:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_VAULTID.value, logger)
        if field_name == ConfigField.CLUSTER_ID:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_CLUSTER_ID.value, logger)
        if field_name == OptionField.CONNECTION_ID:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_CONNECTION_ID.value, logger)
        if field_name == OptionField.CONNECTION_URL:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_CONNECTION_URL.value, logger)
        if field_name == CredentialField.PATH:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_CREDENTIALS_PATH.value, logger)
        if field_name == CredentialField.CREDENTIALS_STRING:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_CREDENTIALS_STRING.value, logger)
        if field_name == CredentialField.TOKEN:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_TOKEN_VALUE.value, logger)
        if field_name == CredentialField.API_KEY:
            log_error_log(SkyflowMessages.ErrorLogs.EMPTY_API_KEY_VALUE.value, logger)
        raise SkyflowError(empty_error, invalid_input_error_code)


def validate_api_key(api_key: str, logger=None) -> bool:
    if not api_key.startswith(ApiKey.SKY_PREFIX):
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_API_KEY.value, logger=logger)
        return False

    if len(api_key) != ApiKey.LENGTH:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_API_KEY.value, logger=logger)
        return False

    return True


def validate_credentials(logger, credentials, config_id_type=None, config_id=None):
    key_present = [k for k in [CredentialField.PATH, CredentialField.TOKEN, CredentialField.CREDENTIALS_STRING, CredentialField.API_KEY] if credentials.get(k)]

    if len(key_present) == 0:
        error_message = (
            SkyflowMessages.Error.INVALID_CREDENTIALS_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            SkyflowMessages.Error.INVALID_CREDENTIALS.value
        )
        log_error_log(error_message, logger)
        raise SkyflowError(error_message, invalid_input_error_code)
    elif len(key_present) > 1:
        error_message = (
            SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED.value
        )
        log_error_log(error_message, logger)
        raise SkyflowError(error_message, invalid_input_error_code)

    if CredentialField.ROLES in credentials:
        validate_required_field(
            logger, credentials, CredentialField.ROLES, list,
            SkyflowMessages.Error.INVALID_ROLES_KEY_TYPE_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_ROLES_KEY_TYPE.value,
            SkyflowMessages.Error.EMPTY_ROLES_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_ROLES.value
        )

    if CredentialField.CONTEXT in credentials:
        validate_required_field(
            logger, credentials, CredentialField.CONTEXT, str,
            SkyflowMessages.Error.EMPTY_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CONTEXT.value,
            SkyflowMessages.Error.INVALID_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CONTEXT.value
        )

    if CredentialField.CREDENTIALS_STRING in credentials:
        validate_required_field(
            logger, credentials, CredentialField.CREDENTIALS_STRING, str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIALS_STRING.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIALS_STRING.value
        )
    elif CredentialField.PATH in credentials:
        validate_required_field(
            logger, credentials, CredentialField.PATH, str,
            SkyflowMessages.Error.EMPTY_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIAL_FILE_PATH.value,
            SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIAL_FILE_PATH.value
        )
    elif CredentialField.TOKEN in credentials:
        validate_required_field(
            logger, credentials, CredentialField.TOKEN, str,
            SkyflowMessages.Error.EMPTY_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_CREDENTIALS_TOKEN.value,
            SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_CREDENTIALS_TOKEN.value
        )
        if is_expired(credentials.get(CredentialField.TOKEN), logger):
            log_error_log(SkyflowMessages.ErrorLogs.INVALID_BEARER_TOKEN.value, logger)
            raise SkyflowError(
                SkyflowMessages.Error.EXPIRED_BEARER_TOKEN.value
                if config_id_type and config_id else SkyflowMessages.Error.EXPIRED_BEARER_TOKEN.value,
                invalid_input_error_code
            )
    elif CredentialField.API_KEY in credentials:
        validate_required_field(
            logger, credentials, CredentialField.API_KEY, str,
            SkyflowMessages.Error.EMPTY_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.EMPTY_API_KEY.value,
            SkyflowMessages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else SkyflowMessages.Error.INVALID_API_KEY.value
        )
        if not validate_api_key(credentials.get(CredentialField.API_KEY), logger):
            raise SkyflowError(SkyflowMessages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
                               if config_id_type and config_id else SkyflowMessages.Error.INVALID_API_KEY.value,
                               invalid_input_error_code)

    if CredentialField.TOKEN_URI_OPTION in credentials:
        token_uri = credentials.get(CredentialField.TOKEN_URI_OPTION)
        if (
            token_uri is None
            or not isinstance(token_uri, str)
            or not is_valid_url(token_uri)
        ):
            log_error_log(SkyflowMessages.ErrorLogs.INVALID_TOKEN_URI.value, logger)
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_URI.value, invalid_input_error_code)


def validate_log_level(logger, log_level):
    if not isinstance(log_level, LogLevel):
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_LOG_LEVEL.value, logger)
        raise SkyflowError(SkyflowMessages.Error.INVALID_LOG_LEVEL.value, invalid_input_error_code)


def validate_keys(logger, config, config_keys):
    for key in config.keys():
        if key not in config_keys:
            log_error_log(SkyflowMessages.ErrorLogs.INVALID_KEY.value.format(key), logger)
            raise SkyflowError(SkyflowMessages.Error.INVALID_KEY.value.format(key), invalid_input_error_code)
