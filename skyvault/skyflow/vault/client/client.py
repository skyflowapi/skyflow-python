from common.utils import get_vault_url
from common.vault.base_vault_client import BaseVaultClient
from skyflow.generated.rest.client import Skyflow


class VaultClient(BaseVaultClient):
    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        return get_vault_url(cluster_id, env, vault_id, logger=logger)

    def initialize_api_client(self, vault_url, bearer_token):
        token_provider = lambda: self._bearer_token if self._bearer_token is not None else bearer_token  # noqa: E731
        self._api_client = Skyflow(base_url=vault_url, token=token_provider)

    def get_records_api(self):
        return self._api_client.records

    def get_tokens_api(self):
        return self._api_client.tokens

    def get_query_api(self):
        return self._api_client.query

    def get_detect_text_api(self):
        return self._api_client.strings

    def get_detect_file_api(self):
        return self._api_client.files
