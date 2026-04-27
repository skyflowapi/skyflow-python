import unittest
from unittest.mock import patch, MagicMock, call
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
    def setUp(self):
        self.vault_client = VaultClient(CONFIG)

    # ------------------------------------------------------------------ #
    # Basic setters / getters                                              #
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

    def test_get_common_skyflow_credentials(self):
        credentials = {"api_key": "dummy_api_key"}
        self.vault_client.set_common_skyflow_credentials(credentials)
        self.assertEqual(self.vault_client.get_common_skyflow_credentials(), credentials)

    def test_get_log_level(self):
        self.vault_client.set_logger("DEBUG", MagicMock())
        self.assertEqual(self.vault_client.get_log_level(), "DEBUG")

    def test_get_logger(self):
        mock_logger = MagicMock()
        self.vault_client.set_logger("INFO", mock_logger)
        self.assertEqual(self.vault_client.get_logger(), mock_logger)

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — first call (slow path)            #
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_first_call(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials
    ):
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_get_vault_url.return_value = "https://test-vault-url.com"

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_called_once_with(
            CONFIG["credentials"], None, logger=None
        )
        mock_get_vault_url.assert_called_once_with(
            CONFIG["cluster_id"], CONFIG["env"], CONFIG["vault_id"], logger=None
        )
        mock_init_api_client.assert_called_once()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — fast path (static token)          #
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_fast_path_api_key(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials
    ):
        """Once initialized with api_key, subsequent calls skip all work."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_get_vault_url.return_value = "https://test-vault-url.com"
        # Side-effect simulates initialize_api_client actually setting __api_client
        mock_init_api_client.side_effect = lambda *_: setattr(
            self.vault_client, "_VaultClient__api_client", MagicMock()
        )

        self.vault_client.initialize_client_configuration()  # first call — slow path
        mock_get_credentials.reset_mock()
        mock_get_vault_url.reset_mock()
        mock_init_api_client.reset_mock()

        self.vault_client.initialize_client_configuration()  # second call — fast path

        mock_get_credentials.assert_not_called()
        mock_get_vault_url.assert_not_called()
        mock_init_api_client.assert_not_called()

    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_fast_path_static_token(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials
    ):
        """Once initialized with a static token, subsequent calls skip all work."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_TOKEN
        mock_get_vault_url.return_value = "https://test-vault-url.com"
        mock_init_api_client.side_effect = lambda *_: setattr(
            self.vault_client, "_VaultClient__api_client", MagicMock()
        )

        self.vault_client.initialize_client_configuration()
        mock_get_credentials.reset_mock()
        mock_get_vault_url.reset_mock()
        mock_init_api_client.reset_mock()

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_not_called()
        mock_get_vault_url.assert_not_called()
        mock_init_api_client.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — fast path (service account)       #
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.is_expired", return_value=False)
    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_fast_path_valid_sa_token(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials, mock_is_expired
    ):
        """Service account with a still-valid token skips get_bearer_token entirely."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_PATH
        mock_get_vault_url.return_value = "https://test-vault-url.com"

        # Seed the cached bearer token as if first call already ran
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__is_static_token = False
        self.vault_client._VaultClient__bearer_token = "cached_sa_token"
        self.vault_client._VaultClient__credentials = CREDENTIALS_WITH_PATH

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_not_called()
        mock_get_vault_url.assert_not_called()
        mock_init_api_client.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — token expiry (no client reinit)   #
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.generate_bearer_token", return_value=("new_sa_token", None))
    @patch("skyflow.vault.client.client.is_expired", return_value=True)
    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_expired_token_no_reinit(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials,
        mock_is_expired, mock_generate_bearer_token
    ):
        """Expired service account token is regenerated in-place; httpx client is NOT recreated."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_PATH
        mock_get_vault_url.return_value = "https://test-vault-url.com"

        # Client already initialized — simulate warm state with an expired token
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__is_static_token = False
        self.vault_client._VaultClient__bearer_token = "expired_sa_token"
        self.vault_client._VaultClient__credentials = CREDENTIALS_WITH_PATH

        self.vault_client.initialize_client_configuration()

        # Token was regenerated
        mock_generate_bearer_token.assert_called_once()
        self.assertEqual(
            self.vault_client._VaultClient__bearer_token, "new_sa_token"
        )
        # httpx client was NOT recreated
        mock_init_api_client.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — config update forces reinit        #
    # ------------------------------------------------------------------ #

    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration_reinit_after_update_config(
        self, mock_init_api_client, mock_get_vault_url, mock_get_credentials
    ):
        """update_config() marks the client stale; next call must recreate it."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_get_vault_url.return_value = "https://test-vault-url.com"

        # Simulate already-initialized client
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__is_static_token = True

        self.vault_client.update_config({"cluster_id": "new_cluster"})
        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_called_once()
        mock_get_vault_url.assert_called_once()
        mock_init_api_client.assert_called_once()

    # ------------------------------------------------------------------ #
    # initialize_api_client — lambda token provider                       #
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
        """Lambda returns __bearer_token when it is set (interceptor behaviour)."""
        self.vault_client._VaultClient__bearer_token = "refreshed_token"
        self.vault_client.initialize_api_client("https://test-vault-url.com", "initial_token")

        _, kwargs = mock_skyflow.call_args
        self.assertEqual(kwargs["token"](), "refreshed_token")

    @patch("skyflow.vault.client.client.Skyflow")
    def test_initialize_api_client_lambda_falls_back_to_initial_token(self, mock_skyflow):
        """Lambda falls back to the initial token when __bearer_token is None."""
        self.vault_client._VaultClient__bearer_token = None
        self.vault_client.initialize_api_client("https://test-vault-url.com", "initial_token")

        _, kwargs = mock_skyflow.call_args
        self.assertEqual(kwargs["token"](), "initial_token")

    # ------------------------------------------------------------------ #
    # get_bearer_token                                                     #
    # ------------------------------------------------------------------ #

    def test_get_bearer_token_with_api_key(self):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_API_KEY)
        self.assertEqual(result, "dummy_api_key")

    def test_get_bearer_token_with_static_token(self):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_TOKEN)
        self.assertEqual(result, "dummy_static_token")

    @patch("skyflow.vault.client.client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_generates_from_path_on_first_call(self, mock_generate):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_called_once()
        self.assertEqual(result, "sa_token")
        self.assertEqual(self.vault_client._VaultClient__bearer_token, "sa_token")

    @patch("skyflow.vault.client.client.generate_bearer_token_from_creds", return_value=("sa_token_str", None))
    @patch("skyflow.vault.client.client.log_info")
    def test_get_bearer_token_generates_from_credentials_string(self, mock_log, mock_generate):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_STRING)
        mock_generate.assert_called_once()
        self.assertEqual(result, "sa_token_str")

    @patch("skyflow.vault.client.client.generate_bearer_token", return_value=("new_token", None))
    @patch("skyflow.vault.client.client.is_expired", return_value=True)
    @patch("skyflow.vault.client.client.log_info")
    def test_get_bearer_token_regenerates_on_expiry(self, mock_log, mock_is_expired, mock_generate):
        """Expired token is regenerated silently — no exception raised."""
        self.vault_client._VaultClient__bearer_token = "expired_token"
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_called_once()
        self.assertEqual(result, "new_token")

    @patch("skyflow.vault.client.client.generate_bearer_token")
    @patch("skyflow.vault.client.client.is_expired", return_value=False)
    @patch("skyflow.vault.client.client.log_info")
    def test_get_bearer_token_reuses_valid_cached_token(self, mock_log, mock_is_expired, mock_generate):
        """Valid cached token is reused without calling generate_bearer_token."""
        self.vault_client._VaultClient__bearer_token = "valid_token"
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_not_called()
        self.assertEqual(result, "valid_token")

    # ------------------------------------------------------------------ #
    # update_config                                                        #
    # ------------------------------------------------------------------ #

    def test_update_config_sets_flag(self):
        self.vault_client.update_config({"credentials": "new_credentials"})
        self.assertTrue(self.vault_client._VaultClient__is_config_updated)
        self.assertEqual(self.vault_client.get_config()["credentials"], "new_credentials")

    # ------------------------------------------------------------------ #
    # API accessor stubs                                                   #
    # ------------------------------------------------------------------ #

    def test_get_records_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_records_api())

    def test_get_tokens_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_tokens_api())

    def test_get_query_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.assertIsNotNone(self.vault_client.get_query_api())


if __name__ == "__main__":
    unittest.main()
