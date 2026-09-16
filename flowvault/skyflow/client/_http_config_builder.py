from skyflow.utils._http_config import (
    TIMEOUT_KEY,
    CONNECT_TIMEOUT_KEY,
    READ_TIMEOUT_KEY,
    WRITE_TIMEOUT_KEY,
    MAX_RETRIES_KEY,
    INITIAL_RETRY_DELAY_MILLIS_KEY,
    MAX_RETRY_DELAY_MILLIS_KEY,
)
from skyflow.utils.validations._validations import validate_http_config_value


class HttpConfigBuilderMixin:
    def __init__(self):
        super().__init__()
        self._client_http_config = {}

    def _set_http_config(self, key, value):
        validate_http_config_value(key, value)
        self._client_http_config[key] = value
        return self

    def timeout(self, seconds):
        return self._set_http_config(TIMEOUT_KEY, seconds)

    def connect_timeout(self, seconds):
        return self._set_http_config(CONNECT_TIMEOUT_KEY, seconds)

    def read_timeout(self, seconds):
        return self._set_http_config(READ_TIMEOUT_KEY, seconds)

    def write_timeout(self, seconds):
        return self._set_http_config(WRITE_TIMEOUT_KEY, seconds)

    def max_retries(self, retries):
        return self._set_http_config(MAX_RETRIES_KEY, retries)

    def initial_retry_delay_millis(self, millis):
        return self._set_http_config(INITIAL_RETRY_DELAY_MILLIS_KEY, millis)

    def max_retry_delay_millis(self, millis):
        return self._set_http_config(MAX_RETRY_DELAY_MILLIS_KEY, millis)

    def _on_vault_client_created(self, vault_client):
        vault_client.set_common_http_config(self._client_http_config)
