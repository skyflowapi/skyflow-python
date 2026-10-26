from common.utils import get_vault_url
from common.vault.base_vault_client import BaseVaultClient
from common.generated.rest.client import SkyflowAuth as DetectSkyflowAuth
from skyflow.generated.rest.client import SkyflowAuth
from skyflow.utils._utils import get_metrics


class VaultClient(BaseVaultClient):
    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        return get_vault_url(cluster_id, env, vault_id, logger=logger)

    def initialize_api_client(self, vault_url, bearer_token):
        token_provider = lambda: self._bearer_token if self._bearer_token is not None else bearer_token  # noqa: E731
        self._api_client = SkyflowAuth(base_url=vault_url, token=token_provider)
        self._detect_api_client = DetectSkyflowAuth(base_url=vault_url, token=token_provider)

    def get_records_api(self):
        return self._api_client.records

    def get_tokens_api(self):
        return self._api_client.tokens

    def get_query_api(self):
        return self._api_client.query

    def get_strings_v2_api(self):
        return self._detect_api_client.strings_v2

    def get_files_v2_api(self):
        return self._detect_api_client.files_v2

    def get_guardrails_v2_api(self):
        return self._detect_api_client.guardrails_v2

    def get_sdk_metrics(self):
        return get_metrics()
