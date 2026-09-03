from common.utils.validations._validations import VALID_VAULT_CONFIG_KEYS

TIMEOUT_KEY = "timeout"
CONNECT_TIMEOUT_KEY = "connect_timeout"
READ_TIMEOUT_KEY = "read_timeout"
WRITE_TIMEOUT_KEY = "write_timeout"
MAX_RETRIES_KEY = "max_retries"
INITIAL_RETRY_DELAY_MILLIS_KEY = "initial_retry_delay_millis"
MAX_RETRY_DELAY_MILLIS_KEY = "max_retry_delay_millis"
VAULT_URL_KEY = "vault_url"

DEFAULT_TIMEOUT = 60
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 10
DEFAULT_WRITE_TIMEOUT = 10
DEFAULT_MAX_RETRIES = 0
DEFAULT_INITIAL_RETRY_DELAY_MILLIS = 500
DEFAULT_MAX_RETRY_DELAY_MILLIS = 2000

POSITIVE_SECOND_KEYS = (TIMEOUT_KEY, CONNECT_TIMEOUT_KEY, READ_TIMEOUT_KEY, WRITE_TIMEOUT_KEY)
NON_NEGATIVE_INT_KEYS = (MAX_RETRIES_KEY, INITIAL_RETRY_DELAY_MILLIS_KEY, MAX_RETRY_DELAY_MILLIS_KEY)

CLIENT_HTTP_CONFIG_KEYS = (*POSITIVE_SECOND_KEYS, *NON_NEGATIVE_INT_KEYS)
VAULT_CONFIG_KEYS = [*VALID_VAULT_CONFIG_KEYS, *CLIENT_HTTP_CONFIG_KEYS, VAULT_URL_KEY]


def resolve_setting(vault_config, common_config, key, default):
    if vault_config is not None and key in vault_config:
        return vault_config[key]
    if common_config is not None and key in common_config:
        return common_config[key]
    return default
