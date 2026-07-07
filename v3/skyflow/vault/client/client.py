from common.vault.base_vault_client import BaseVaultClient
from skyflow.generated.rest.client import SkyflowAuth
from skyflow.utils import get_vault_url


class VaultClient(BaseVaultClient):
    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        return get_vault_url(cluster_id, env, vault_id, logger=logger)

    def initialize_api_client(self, vault_url, bearer_token):
        # SkyflowAuth has no `token` param -- auth is injected per-call instead (see
        # FlowVaultController._build_headers).
        self._api_client = SkyflowAuth(base_url=vault_url)

    def get_insert_api(self):
        return self._api_client.flowservice
