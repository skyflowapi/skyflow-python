import httpx

from common.vault.base_vault_client import BaseVaultClient
from skyflow_flowvault.generated.rest.client import SkyflowAuth, AsyncSkyflowAuth
from skyflow_flowvault.utils import get_vault_url
from skyflow_flowvault.utils._http_config import (
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
    resolve_setting,
)
from skyflow_flowvault.utils._retry import RetryTransport, AsyncRetryTransport


class VaultClient(BaseVaultClient):
    def __init__(self, config):
        super().__init__(config)
        self._common_http_config = {}

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

    def initialize_api_client(self, vault_url, bearer_token):
        timeout = self._build_timeout()
        max_retries, initial_millis, max_millis, call_timeout = self._retry_params()
        sync_client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            transport=RetryTransport(httpx.HTTPTransport(), max_retries, initial_millis, max_millis, call_timeout),
        )
        async_client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            transport=AsyncRetryTransport(httpx.AsyncHTTPTransport(), max_retries, initial_millis, max_millis, call_timeout),
        )
        self._api_client = SkyflowAuth(base_url=vault_url, token=bearer_token or "", httpx_client=sync_client)
        self._async_api_client = AsyncSkyflowAuth(base_url=vault_url, token=bearer_token or "", httpx_client=async_client)

    def get_records_api(self):
        return self._api_client.records

    def get_tokens_api(self):
        return self._api_client.tokens

    def get_query_api(self):
        return self._api_client.query

    def get_async_records_api(self):
        return self._async_api_client.records

    def get_async_tokens_api(self):
        return self._async_api_client.tokens
