from common.errors import SkyflowError
from common.service_account import is_expired
from common.service_account._utils import _validate_and_resolve_ctx
from common.utils import SkyflowMessages
from common.utils.constants import ApiKey, ConfigField, CredentialField, OptionField
from common.utils.enums import Env, LogLevel
from common.utils.logger import log_error_log, log_info
from common.utils._helpers import is_valid_url

invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

VALID_VAULT_CONFIG_KEYS = [
    ConfigField.VAULT_ID,
    ConfigField.CLUSTER_ID,
    ConfigField.CREDENTIALS,
    ConfigField.ENV,
]


def validate_required_field(logger, config, field_name, expected_type, empty_error, invalid_error, messages=None):
    messages = messages or SkyflowMessages
    field_value = config.get(field_name)

    if field_name not in config or not isinstance(field_value, expected_type):
        if field_name == ConfigField.VAULT_ID:
            log_error_log(messages.ErrorLogs.VAULTID_IS_REQUIRED.value, logger)
        if field_name == ConfigField.CLUSTER_ID:
            log_error_log(messages.ErrorLogs.CLUSTER_ID_IS_REQUIRED.value, logger)
        if field_name == OptionField.CONNECTION_ID:
            log_error_log(messages.ErrorLogs.CONNECTION_ID_IS_REQUIRED.value, logger)
        if field_name == OptionField.CONNECTION_URL:
            log_error_log(messages.ErrorLogs.INVALID_CONNECTION_URL.value, logger)
        raise SkyflowError(invalid_error, invalid_input_error_code)

    if isinstance(field_value, str) and not field_value.strip():
        if field_name == ConfigField.VAULT_ID:
            log_error_log(messages.ErrorLogs.EMPTY_VAULTID.value, logger)
        if field_name == ConfigField.CLUSTER_ID:
            log_error_log(messages.ErrorLogs.EMPTY_CLUSTER_ID.value, logger)
        if field_name == OptionField.CONNECTION_ID:
            log_error_log(messages.ErrorLogs.EMPTY_CONNECTION_ID.value, logger)
        if field_name == OptionField.CONNECTION_URL:
            log_error_log(messages.ErrorLogs.EMPTY_CONNECTION_URL.value, logger)
        if field_name == CredentialField.PATH:
            log_error_log(messages.ErrorLogs.EMPTY_CREDENTIALS_PATH.value, logger)
        if field_name == CredentialField.CREDENTIALS_STRING:
            log_error_log(messages.ErrorLogs.EMPTY_CREDENTIALS_STRING.value, logger)
        if field_name == CredentialField.TOKEN:
            log_error_log(messages.ErrorLogs.EMPTY_TOKEN_VALUE.value, logger)
        if field_name == CredentialField.API_KEY:
            log_error_log(messages.ErrorLogs.EMPTY_API_KEY_VALUE.value, logger)
        raise SkyflowError(empty_error, invalid_input_error_code)


def validate_api_key(api_key: str, logger=None, messages=None) -> bool:
    messages = messages or SkyflowMessages
    if not api_key.startswith(ApiKey.SKY_PREFIX):
        log_error_log(messages.ErrorLogs.INVALID_API_KEY.value, logger=logger)
        return False

    if len(api_key) != ApiKey.LENGTH:
        log_error_log(messages.ErrorLogs.INVALID_API_KEY.value, logger=logger)
        return False

    return True


def validate_token_options(logger, credentials, config_id_type=None, config_id=None, messages=None):
    messages = messages or SkyflowMessages

    if CredentialField.ROLES in credentials:
        empty_roles_error = (
            messages.Error.EMPTY_ROLES_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_ROLES.value
        )
        validate_required_field(
            logger, credentials, CredentialField.ROLES, list,
            empty_roles_error,
            messages.Error.INVALID_ROLES_KEY_TYPE_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_ROLES_KEY_TYPE.value,
            messages=messages)
        if not credentials.get(CredentialField.ROLES):
            raise SkyflowError(empty_roles_error, invalid_input_error_code)

        invalid_role_element_error = (
            messages.Error.INVALID_ROLE_ELEMENT_TYPE_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_ROLE_ELEMENT_TYPE.value
        )
        for role in credentials.get(CredentialField.ROLES):
            if not isinstance(role, str) or not role.strip():
                raise SkyflowError(invalid_role_element_error, invalid_input_error_code)

    if CredentialField.CONTEXT in credentials:
        empty_context_error = (
            messages.Error.EMPTY_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_CONTEXT.value
        )
        validate_required_field(
            logger, credentials, CredentialField.CONTEXT, (str, dict, bool, int, float),
            empty_context_error,
            messages.Error.INVALID_CONTEXT_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_CONTEXT.value,
            messages=messages)
        context = credentials.get(CredentialField.CONTEXT)
        if isinstance(context, dict):
            if not context:
                raise SkyflowError(empty_context_error, invalid_input_error_code)
            _validate_and_resolve_ctx(context, messages=messages)

def validate_credentials(logger, credentials, config_id_type=None, config_id=None, messages=None):
    messages = messages or SkyflowMessages
    key_present = [k for k in [CredentialField.PATH, CredentialField.TOKEN, CredentialField.CREDENTIALS_STRING, CredentialField.API_KEY] if credentials.get(k)]

    if len(key_present) == 0:
        error_message = (
            messages.Error.INVALID_CREDENTIALS_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            messages.Error.INVALID_CREDENTIALS.value
        )
        log_error_log(error_message, logger)
        raise SkyflowError(error_message, invalid_input_error_code)
    elif len(key_present) > 1:
        error_message = (
            messages.Error.MULTIPLE_CREDENTIALS_PASSED_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else
            messages.Error.MULTIPLE_CREDENTIALS_PASSED.value
        )
        log_error_log(error_message, logger)
        raise SkyflowError(error_message, invalid_input_error_code)

    validate_token_options(logger, credentials, config_id_type, config_id, messages=messages)

    if CredentialField.CREDENTIALS_STRING in credentials:
        validate_required_field(
            logger, credentials, CredentialField.CREDENTIALS_STRING, str,
            messages.Error.EMPTY_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_CREDENTIALS_STRING.value,
            messages.Error.INVALID_CREDENTIALS_STRING_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_CREDENTIALS_STRING.value,
        messages=messages)
    elif CredentialField.PATH in credentials:
        validate_required_field(
            logger, credentials, CredentialField.PATH, str,
            messages.Error.EMPTY_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_CREDENTIAL_FILE_PATH.value,
            messages.Error.INVALID_CREDENTIAL_FILE_PATH_IN_CONFIG.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_CREDENTIAL_FILE_PATH.value,
        messages=messages)
    elif CredentialField.TOKEN in credentials:
        validate_required_field(
            logger, credentials, CredentialField.TOKEN, str,
            messages.Error.EMPTY_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_CREDENTIALS_TOKEN.value,
            messages.Error.INVALID_CREDENTIALS_TOKEN.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_CREDENTIALS_TOKEN.value,
        messages=messages)
        if is_expired(credentials.get(CredentialField.TOKEN), logger):
            log_error_log(messages.ErrorLogs.INVALID_BEARER_TOKEN.value, logger)
            raise SkyflowError(
                messages.Error.EXPIRED_BEARER_TOKEN.value
                if config_id_type and config_id else messages.Error.EXPIRED_BEARER_TOKEN.value,
                invalid_input_error_code
            )
    elif CredentialField.API_KEY in credentials:
        validate_required_field(
            logger, credentials, CredentialField.API_KEY, str,
            messages.Error.EMPTY_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.EMPTY_API_KEY.value,
            messages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
            if config_id_type and config_id else messages.Error.INVALID_API_KEY.value,
        messages=messages)
        if not validate_api_key(credentials.get(CredentialField.API_KEY), logger, messages=messages):
            raise SkyflowError(messages.Error.INVALID_API_KEY.value.format(config_id_type, config_id)
                               if config_id_type and config_id else messages.Error.INVALID_API_KEY.value,
                               invalid_input_error_code)

    if CredentialField.TOKEN_URI_OPTION in credentials:
        token_uri = credentials.get(CredentialField.TOKEN_URI_OPTION)
        if (
            token_uri is None
            or not isinstance(token_uri, str)
            or not is_valid_url(token_uri)
        ):
            log_error_log(messages.ErrorLogs.INVALID_TOKEN_URI.value, logger)
            raise SkyflowError(messages.Error.INVALID_TOKEN_URI.value, invalid_input_error_code)


def validate_log_level(logger, log_level, messages=None):
    messages = messages or SkyflowMessages
    if not isinstance(log_level, LogLevel):
        log_error_log(messages.ErrorLogs.INVALID_LOG_LEVEL.value, logger)
        raise SkyflowError(messages.Error.INVALID_LOG_LEVEL.value, invalid_input_error_code)


def validate_keys(logger, config, config_keys, messages=None):
    messages = messages or SkyflowMessages
    for key in config.keys():
        if key not in config_keys:
            log_error_log(messages.ErrorLogs.INVALID_KEY.value.format(key), logger)
            raise SkyflowError(messages.Error.INVALID_KEY.value.format(key), invalid_input_error_code)


def validate_non_empty_string_list(logger, value, error):
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise SkyflowError(error, invalid_input_error_code)


def validate_vault_config(logger, config, messages=None, allowed_keys=None):
    messages = messages or SkyflowMessages
    allowed_keys = allowed_keys or VALID_VAULT_CONFIG_KEYS
    log_info(messages.Info.VALIDATING_VAULT_CONFIG.value, logger)
    validate_keys(logger, config, allowed_keys, messages=messages)

    validate_required_field(
        logger, config, ConfigField.VAULT_ID, str,
        messages.Error.EMPTY_VAULT_ID.value,
        messages.Error.INVALID_VAULT_ID.value,
        messages=messages
    )
    vault_id = config.get(ConfigField.VAULT_ID)

    validate_required_field(
        logger, config, ConfigField.CLUSTER_ID, str,
        messages.Error.EMPTY_CLUSTER_ID.value.format(vault_id),
        messages.Error.INVALID_CLUSTER_ID.value.format(vault_id),
        messages=messages
    )

    if ConfigField.CREDENTIALS in config and not config.get(ConfigField.CREDENTIALS):
        raise SkyflowError(messages.Error.EMPTY_CREDENTIALS.value.format("vault", vault_id), invalid_input_error_code)

    if ConfigField.CREDENTIALS in config and config.get(ConfigField.CREDENTIALS):
        validate_credentials(logger, config.get(ConfigField.CREDENTIALS), "vault", vault_id, messages=messages)

    if ConfigField.ENV in config and config.get(ConfigField.ENV) not in Env:
        log_error_log(messages.ErrorLogs.ENV_IS_REQUIRED.value, logger)
        raise SkyflowError(messages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    return True


def validate_update_vault_config(logger, config, messages=None, allowed_keys=None):
    """Credentials are required on update (unlike on initial add, where they're optional)."""
    messages = messages or SkyflowMessages
    allowed_keys = allowed_keys or VALID_VAULT_CONFIG_KEYS
    validate_keys(logger, config, allowed_keys, messages=messages)

    validate_required_field(
        logger, config, ConfigField.VAULT_ID, str,
        messages.Error.EMPTY_VAULT_ID.value,
        messages.Error.INVALID_VAULT_ID.value,
        messages=messages
    )
    vault_id = config.get(ConfigField.VAULT_ID)

    if ConfigField.CLUSTER_ID in config and not config.get(ConfigField.CLUSTER_ID):
        raise SkyflowError(messages.Error.INVALID_CLUSTER_ID.value.format(vault_id), invalid_input_error_code)

    if ConfigField.ENV in config and config.get(ConfigField.ENV) not in Env:
        raise SkyflowError(messages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    if ConfigField.CREDENTIALS not in config:
        raise SkyflowError(messages.Error.EMPTY_CREDENTIALS.value.format("vault", vault_id), invalid_input_error_code)

    validate_credentials(logger, config.get(ConfigField.CREDENTIALS), "vault", vault_id, messages=messages)

    return True
