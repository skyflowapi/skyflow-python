from common.vault.base_vault_client import BaseVaultClient
from skyflow_flowvault.generated.rest.client import SkyflowAuth, AsyncSkyflowAuth
from skyflow_flowvault.utils import get_vault_url


class VaultClient(BaseVaultClient):
    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        return get_vault_url(cluster_id, env, vault_id, logger=logger)

    def initialize_api_client(self, vault_url, bearer_token):
        self._api_client = SkyflowAuth(base_url=vault_url, token=bearer_token or "")
        self._async_api_client = AsyncSkyflowAuth(base_url=vault_url, token=bearer_token or "")

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
