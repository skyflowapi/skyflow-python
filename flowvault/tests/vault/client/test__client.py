import unittest
from unittest.mock import patch, MagicMock

from common.utils.enums import Env
from common.vault.base_vault_client import BaseVaultClient
from skyflow_flowvault.vault.client.client import VaultClient


class TestVaultClient(unittest.TestCase):
    def setUp(self):
        self.vault_client = VaultClient({"vault_id": "test_vault"})

    def test_is_a_base_vault_client(self):
        self.assertIsInstance(self.vault_client, BaseVaultClient)

    # ------------------------------------------------------------------ #
    # resolve_vault_url — v3's own domain (skyvault.skyflowapis.*), confirmed
    # to differ from v2's (vault.skyflowapis.*) for the same cluster_id/env
    # -- reusing v2's derivation here 404'd. All four envs confirmed.
    # ------------------------------------------------------------------ #

    def test_resolve_vault_url_uses_v3_skyvault_domain_dev(self):
        url = self.vault_client.resolve_vault_url("qhdmceurtnlz", Env.DEV, "myvault")
        self.assertEqual(url, "https://qhdmceurtnlz.skyvault.skyflowapis.dev")

    def test_resolve_vault_url_uses_v3_skyvault_domain_prod(self):
        url = self.vault_client.resolve_vault_url("qhdmceurtnlz", Env.PROD, "myvault")
        self.assertEqual(url, "https://qhdmceurtnlz.skyvault.skyflowapis.com")

    def test_resolve_vault_url_uses_v3_skyvault_domain_sandbox(self):
        url = self.vault_client.resolve_vault_url("qhdmceurtnlz", Env.SANDBOX, "myvault")
        self.assertEqual(url, "https://qhdmceurtnlz.skyvault.skyflowapis-preview.com")

    def test_resolve_vault_url_uses_v3_skyvault_domain_stage(self):
        url = self.vault_client.resolve_vault_url("qhdmceurtnlz", Env.STAGE, "myvault")
        self.assertEqual(url, "https://qhdmceurtnlz.skyvault.skyflowapis.tech")

    @patch("skyflow_flowvault.vault.client.client.SkyflowAuth")
    def test_initialize_api_client_passes_base_url_and_token(self, mock_skyflow_auth):
        self.vault_client.initialize_api_client("https://test-vault-url.com", "some_bearer_token")

        _, kwargs = mock_skyflow_auth.call_args
        self.assertEqual(kwargs.get("base_url"), "https://test-vault-url.com")
        self.assertEqual(kwargs.get("token"), "some_bearer_token")

    def test_get_records_api_returns_records(self):
        self.vault_client._api_client = MagicMock()
        result = self.vault_client.get_records_api()
        self.assertEqual(result, self.vault_client._api_client.records)

    def test_get_tokens_api_returns_tokens(self):
        self.vault_client._api_client = MagicMock()
        result = self.vault_client.get_tokens_api()
        self.assertEqual(result, self.vault_client._api_client.tokens)

    def test_get_query_api_returns_query(self):
        self.vault_client._api_client = MagicMock()
        result = self.vault_client.get_query_api()
        self.assertEqual(result, self.vault_client._api_client.query)

    def test_get_async_records_api_returns_records(self):
        self.vault_client._async_api_client = MagicMock()
        result = self.vault_client.get_async_records_api()
        self.assertEqual(result, self.vault_client._async_api_client.records)

    def test_get_async_tokens_api_returns_tokens(self):
        self.vault_client._async_api_client = MagicMock()
        result = self.vault_client.get_async_tokens_api()
        self.assertEqual(result, self.vault_client._async_api_client.tokens)


if __name__ == "__main__":
    unittest.main()
