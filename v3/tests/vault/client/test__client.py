import unittest
from unittest.mock import patch, MagicMock

from common.utils.enums import Env
from common.vault.base_vault_client import BaseVaultClient
from skyflow.vault.client.client import VaultClient


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

    @patch("skyflow.vault.client.client.SkyflowAuth")
    def test_initialize_api_client_does_not_pass_token(self, mock_skyflow_auth):
        """v3's generated client has no `token` param at all -- unlike v2, nothing should be
        baked in at construction time; auth is injected per-call instead (see Vault._build_headers)."""
        self.vault_client.initialize_api_client("https://test-vault-url.com", "some_bearer_token")

        _, kwargs = mock_skyflow_auth.call_args
        self.assertEqual(kwargs.get("base_url"), "https://test-vault-url.com")
        self.assertNotIn("token", kwargs)

    def test_get_insert_api_returns_flowservice(self):
        self.vault_client._api_client = MagicMock()
        result = self.vault_client.get_insert_api()
        self.assertEqual(result, self.vault_client._api_client.flowservice)


if __name__ == "__main__":
    unittest.main()
