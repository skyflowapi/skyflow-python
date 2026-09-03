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

    # ------------------------------------------------------------------ #
    # HTTP config resolution (vault -> client-wide -> default) + vault_url
    # ------------------------------------------------------------------ #

    def test_vault_url_override_wins_over_derivation(self):
        client = VaultClient({"vault_id": "v", "vault_url": "https://override.example.com"})
        self.assertEqual(client.resolve_vault_url("cluster", Env.PROD, "v"), "https://override.example.com")

    def test_resolve_precedence_vault_then_common_then_default(self):
        client = VaultClient({"vault_id": "v", "read_timeout": 22})
        client.set_common_http_config({"read_timeout": 5, "connect_timeout": 7})
        self.assertEqual(client._resolve("read_timeout", 10), 22)     # per-vault wins
        self.assertEqual(client._resolve("connect_timeout", 10), 7)   # falls to client-wide
        self.assertEqual(client._resolve("write_timeout", 10), 10)    # falls to default

    def test_build_timeout_uses_resolved_values(self):
        client = VaultClient({"vault_id": "v", "connect_timeout": 3, "read_timeout": 8, "write_timeout": 4})
        timeout = client._build_timeout()
        self.assertEqual(timeout.connect, 3)
        self.assertEqual(timeout.read, 8)
        self.assertEqual(timeout.write, 4)
        self.assertEqual(timeout.pool, 8)

    def test_retry_params_defaults_and_overrides(self):
        client = VaultClient({"vault_id": "v"})
        self.assertEqual(client._retry_params(), (0, 500, 2000, 60))
        client2 = VaultClient({
            "vault_id": "v", "max_retries": 3, "initial_retry_delay_millis": 100,
            "max_retry_delay_millis": 5000, "timeout": 30,
        })
        self.assertEqual(client2._retry_params(), (3, 100, 5000, 30))

    def test_set_common_http_config_none_is_empty(self):
        client = VaultClient({"vault_id": "v"})
        client.set_common_http_config(None)
        self.assertEqual(client._resolve("timeout", 60), 60)


if __name__ == "__main__":
    unittest.main()
