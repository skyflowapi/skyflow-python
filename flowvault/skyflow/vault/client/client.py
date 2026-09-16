import httpx

from common.vault.base_vault_client import BaseVaultClient
from skyflow.generated.rest.client import SkyflowAuth
from skyflow.utils import get_vault_url
from skyflow.utils._http_config import (
    TIMEOUT_KEY,
    CONNECT_TIMEOUT_KEY,
    READ_TIMEOUT_KEY,
    WRITE_TIMEOUT_KEY,
    MAX_RETRIES_KEY,
    INITIAL_RETRY_DELAY_MILLIS_KEY,
    MAX_RETRY_DELAY_MILLIS_KEY,
    VAULT_URL_KEY,
    DEFAULT_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_WRITE_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_INITIAL_RETRY_DELAY_MILLIS,
    DEFAULT_MAX_RETRY_DELAY_MILLIS,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    DEFAULT_KEEPALIVE_EXPIRY,
    resolve_setting,
)
from skyflow.utils._retry import RetryTransport


class VaultClient(BaseVaultClient):
    def __init__(self, config):
        super().__init__(config)
        self._common_http_config = {}
        self._sync_httpx_client = None

    def set_common_http_config(self, common_http_config):
        self._common_http_config = common_http_config or {}

    def _resolve(self, key, default):
        return resolve_setting(self._config, self._common_http_config, key, default)

    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        override = self._config.get(VAULT_URL_KEY)
        if override:
            return override
        return get_vault_url(cluster_id, env, vault_id, logger=logger)

    def _build_timeout(self):
        read = self._resolve(READ_TIMEOUT_KEY, DEFAULT_READ_TIMEOUT)
        return httpx.Timeout(
            connect=self._resolve(CONNECT_TIMEOUT_KEY, DEFAULT_CONNECT_TIMEOUT),
            read=read,
            write=self._resolve(WRITE_TIMEOUT_KEY, DEFAULT_WRITE_TIMEOUT),
            pool=read,
        )

    def _retry_params(self):
        return (
            self._resolve(MAX_RETRIES_KEY, DEFAULT_MAX_RETRIES),
            self._resolve(INITIAL_RETRY_DELAY_MILLIS_KEY, DEFAULT_INITIAL_RETRY_DELAY_MILLIS),
            self._resolve(MAX_RETRY_DELAY_MILLIS_KEY, DEFAULT_MAX_RETRY_DELAY_MILLIS),
            self._resolve(TIMEOUT_KEY, DEFAULT_TIMEOUT),
        )

    def _build_limits(self):
        return httpx.Limits(
            max_connections=DEFAULT_MAX_CONNECTIONS,
            max_keepalive_connections=DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
            keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
        )

    def initialize_api_client(self, vault_url, bearer_token):
        self.__close_httpx_clients()
        timeout = self._build_timeout()
        limits = self._build_limits()
        max_retries, initial_millis, max_millis, call_timeout = self._retry_params()
        sync_client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            transport=RetryTransport(httpx.HTTPTransport(limits=limits), max_retries, initial_millis, max_millis, call_timeout),
        )
        self._sync_httpx_client = sync_client
        self._api_client = SkyflowAuth(base_url=vault_url, token=bearer_token or "", httpx_client=sync_client)

    def close(self):
        self.__close_httpx_clients()
        self._api_client = None

    def __close_httpx_clients(self):
        sync_client = self._sync_httpx_client
        if sync_client is not None:
            try:
                sync_client.close()
            except Exception:
                pass
        self._sync_httpx_client = None

    def get_records_api(self):
        return self._api_client.records

    def get_tokens_api(self):
        return self._api_client.tokens
