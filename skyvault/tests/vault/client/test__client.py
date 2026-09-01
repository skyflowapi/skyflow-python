import unittest
from unittest.mock import patch, MagicMock

from common.utils.enums import Env
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.vault.client.client import VaultClient

CONFIG = {
    "credentials": "some_credentials",
    "cluster_id": "test_cluster_id",
    "env": "test_env",
    "vault_id": "test_vault_id",
    "roles": ["role_id_1", "role_id_2"],
    "ctx": "context"
}

CREDENTIALS_WITH_API_KEY = {"api_key": "dummy_api_key"}
CREDENTIALS_WITH_TOKEN = {"token": "dummy_static_token"}
CREDENTIALS_WITH_PATH = {"path": "/some/path/credentials.json"}
CREDENTIALS_WITH_STRING = {"credentials_string": '{"clientID": "x"}'}


class TestVaultClient(unittest.TestCase):
    """v2-specific VaultClient coverage.

    Shared logic (initialize_client_configuration, get_bearer_token, credential-resolution
    fast paths, update_config) moved to common.vault.base_vault_client.BaseVaultClient and is
    covered by common/tests/vault/test_base_vault_client.py instead -- those scenarios used to
    live here, patching names at this module's path, but the code they exercise no longer runs
    from this module. What remains here is what's genuinely still v2-specific: the
    initialize_api_client() lambda/Skyflow-construction override, and the resource accessors.
    """

    def setUp(self):
        self.vault_client = VaultClient(CONFIG)

    # ------------------------------------------------------------------ #
    # Basic setters / getters (inherited from BaseVaultClient, but exercised
    # here too as a cheap smoke test that the subclass wiring works)
    # ------------------------------------------------------------------ #

    def test_set_common_skyflow_credentials(self):
        credentials = {"api_key": "dummy_api_key"}
        self.vault_client.set_common_skyflow_credentials(credentials)
        self.assertEqual(self.vault_client.get_common_skyflow_credentials(), credentials)

    def test_set_logger(self):
        mock_logger = MagicMock()
        self.vault_client.set_logger("INFO", mock_logger)
        self.assertEqual(self.vault_client.get_log_level(), "INFO")
        self.assertEqual(self.vault_client.get_logger(), mock_logger)

    def test_get_vault_id(self):
        self.assertEqual(self.vault_client.get_vault_id(), CONFIG["vault_id"])

    def test_get_config(self):
        self.assertEqual(self.vault_client.get_config(), CONFIG)

    # ------------------------------------------------------------------ #
    # resolve_vault_url — v2's own domain (vault.skyflowapis.*), the OTHER
    # hook v2 overrides. Regression-pins the exact host v2 must keep hitting.
    # ------------------------------------------------------------------ #

    def test_resolve_vault_url_uses_v2_domain(self):
        url = self.vault_client.resolve_vault_url("mycluster", Env.PROD, "myvault")
        self.assertEqual(url, "https://mycluster.vault.skyflowapis.com")

    # ------------------------------------------------------------------ #
    # initialize_api_client — lambda token provider (v2-specific: this is
    # the one hook v2 actually overrides)
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.Skyflow")
    def test_initialize_api_client_passes_callable_token(self, mock_skyflow):
        """initialize_api_client must pass a callable (lambda) as token, not a string."""
        self.vault_client.initialize_api_client("https://test-vault-url.com", "initial_token")

        args, kwargs = mock_skyflow.call_args
        self.assertEqual(kwargs["base_url"], "https://test-vault-url.com")
        self.assertTrue(callable(kwargs["token"]), "token must be a callable (lambda)")

    @patch("skyflow.vault.client.client.Skyflow")
    def test_initialize_api_client_lambda_returns_cached_bearer_token(self, mock_skyflow):
        """Lambda returns _bearer_token when it is set (interceptor behaviour)."""
        self.vault_client._bearer_token = "refreshed_token"
        self.vault_client.initialize_api_client("https://test-vault-url.com", "initial_token")

        _, kwargs = mock_skyflow.call_args
        self.assertEqual(kwargs["token"](), "refreshed_token")

    @patch("skyflow.vault.client.client.Skyflow")
    def test_initialize_api_client_lambda_falls_back_to_initial_token(self, mock_skyflow):
        """Lambda falls back to the initial token when _bearer_token is None."""
        self.vault_client._bearer_token = None
        self.vault_client.initialize_api_client("https://test-vault-url.com", "initial_token")

        _, kwargs = mock_skyflow.call_args
        self.assertEqual(kwargs["token"](), "initial_token")

    # ------------------------------------------------------------------ #
    # API accessor stubs (v2-specific: v3 doesn't have these)
    # ------------------------------------------------------------------ #

    def test_get_records_api(self):
        self.vault_client._api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_records_api())

    def test_get_tokens_api(self):
        self.vault_client._api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_tokens_api())

    def test_get_query_api(self):
        self.vault_client._api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_query_api())

    def test_get_detect_text_api(self):
        self.vault_client._api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_detect_text_api())

    def test_get_detect_file_api(self):
        self.vault_client._api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_detect_file_api())


if __name__ == "__main__":
    unittest.main()
