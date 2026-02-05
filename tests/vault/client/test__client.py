import unittest
from unittest.mock import patch, MagicMock

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

class TestVaultClient(unittest.TestCase):
    def setUp(self):
        self.vault_client = VaultClient(CONFIG)

    def test_set_common_skyflow_credentials(self):
        credentials = {"api_key": "dummy_api_key"}
        self.vault_client.set_common_skyflow_credentials(credentials)
        self.assertEqual(self.vault_client.get_common_skyflow_credentials(), credentials)

    def test_set_logger(self):
        mock_logger = MagicMock()
        self.vault_client.set_logger("INFO", mock_logger)
        self.assertEqual(self.vault_client.get_log_level(), "INFO")
        self.assertEqual(self.vault_client.get_logger(), mock_logger)

    @patch("skyflow.vault.client.client.get_credentials")
    @patch("skyflow.vault.client.client.get_vault_url")
    @patch("skyflow.vault.client.client.VaultClient.initialize_api_client")
    def test_initialize_client_configuration(self, mock_init_api_client, mock_get_vault_url, mock_get_credentials):
        mock_get_credentials.return_value = (CREDENTIALS_WITH_API_KEY)
        mock_get_vault_url.return_value = "https://test-vault-url.com"

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_called_once_with(CONFIG["credentials"], None, logger=None)
        mock_get_vault_url.assert_called_once_with(CONFIG["cluster_id"], CONFIG["env"], CONFIG["vault_id"], logger=None)
        mock_init_api_client.assert_called_once()

    @patch("skyflow.vault.client.client.Skyflow")
    def test_initialize_api_client(self, mock_api_client):
        self.vault_client.initialize_api_client("https://test-vault-url.com", "dummy_token")
        mock_api_client.assert_called_once_with(base_url="https://test-vault-url.com", token="dummy_token")

    def test_get_records_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__api_client.records = MagicMock()
        records_api = self.vault_client.get_records_api()
        self.assertIsNotNone(records_api)

    def test_get_tokens_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__api_client.tokens = MagicMock()
        tokens_api = self.vault_client.get_tokens_api()
        self.assertIsNotNone(tokens_api)

    def test_get_query_api(self):
        self.vault_client._VaultClient__api_client = MagicMock()
        self.vault_client._VaultClient__api_client.query = MagicMock()
        query_api = self.vault_client.get_query_api()
        self.assertIsNotNone(query_api)

    def test_get_vault_id(self):
        self.assertEqual(self.vault_client.get_vault_id(), CONFIG["vault_id"])

    @patch("skyflow.vault.client.client.generate_bearer_token")
    @patch("skyflow.vault.client.client.generate_bearer_token_from_creds")
    @patch("skyflow.vault.client.client.log_info")
    def test_get_bearer_token_with_api_key(self, mock_log_info, mock_generate_bearer_token,
                                           mock_generate_bearer_token_from_creds):
        token = self.vault_client.get_bearer_token(CREDENTIALS_WITH_API_KEY)
        self.assertEqual(token, CREDENTIALS_WITH_API_KEY["api_key"])

    def test_update_config(self):
        new_config = {"credentials": "new_credentials"}
        self.vault_client.update_config(new_config)
        self.assertTrue(self.vault_client._VaultClient__is_config_updated)
        self.assertEqual(self.vault_client.get_config()["credentials"], "new_credentials")

    def test_get_config(self):
        self.assertEqual(self.vault_client.get_config(), CONFIG)

    def test_get_common_skyflow_credentials(self):
        credentials = {"api_key": "dummy_api_key"}
        self.vault_client.set_common_skyflow_credentials(credentials)
        self.assertEqual(self.vault_client.get_common_skyflow_credentials(), credentials)

    def test_get_log_level(self):
        log_level = "DEBUG"
        self.vault_client.set_logger(log_level, MagicMock())
        self.assertEqual(self.vault_client.get_log_level(), log_level)

    def test_get_logger(self):
        mock_logger = MagicMock()
        self.vault_client.set_logger("INFO", mock_logger)
        self.assertEqual(self.vault_client.get_logger(), mock_logger)

    @patch("skyflow.vault.client.client.is_expired")
    @patch("skyflow.vault.client.client.generate_bearer_token")
    def test_get_bearer_token_expired_token_raises_error(self, mock_generate_bearer_token, mock_is_expired):
        """Test that expired token raises SkyflowError."""
        credentials = {"path": "/path/to/credentials.json"}
        mock_generate_bearer_token.return_value = ("expired_token", None)
        mock_is_expired.return_value = True

        with self.assertRaises(SkyflowError) as context:
            self.vault_client.get_bearer_token(credentials)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.EXPIRED_TOKEN.value)
        self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)
        self.assertTrue(self.vault_client._VaultClient__is_config_updated)

    @patch("skyflow.vault.client.client.is_expired")
    @patch("skyflow.vault.client.client.generate_bearer_token_from_creds")
    def test_get_bearer_token_expired_token_from_creds_string_raises_error(self, mock_generate_bearer_token_from_creds, mock_is_expired):
        """Test that expired token from credentials string raises SkyflowError."""
        credentials = {"credentials_string": '{"key": "value"}'}
        mock_generate_bearer_token_from_creds.return_value = ("expired_token", None)
        mock_is_expired.return_value = True

        with self.assertRaises(SkyflowError) as context:
            self.vault_client.get_bearer_token(credentials)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.EXPIRED_TOKEN.value)
        self.assertEqual(context.exception.http_code, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)
        self.assertTrue(self.vault_client._VaultClient__is_config_updated)

    @patch("skyflow.vault.client.client.is_expired")
    @patch("skyflow.vault.client.client.generate_bearer_token")
    def test_get_bearer_token_reuses_valid_token(self, mock_generate_bearer_token, mock_is_expired):
        """Test that valid bearer token is reused."""
        credentials = {"path": "/path/to/credentials.json"}
        mock_generate_bearer_token.return_value = ("valid_token", None)
        mock_is_expired.return_value = False

        token1 = self.vault_client.get_bearer_token(credentials)
        self.assertEqual(token1, "valid_token")
        mock_generate_bearer_token.assert_called_once()

        token2 = self.vault_client.get_bearer_token(credentials)
        self.assertEqual(token2, "valid_token")
        mock_generate_bearer_token.assert_called_once()

    @patch("skyflow.vault.client.client.is_expired")
    @patch("skyflow.vault.client.client.generate_bearer_token")
    def test_get_bearer_token_regenerates_after_config_update(self, mock_generate_bearer_token, mock_is_expired):
        """Test that bearer token is regenerated after config update."""
        credentials = {"path": "/path/to/credentials.json"}
        mock_generate_bearer_token.side_effect = [("first_token", None), ("second_token", None)]
        mock_is_expired.return_value = False

        token1 = self.vault_client.get_bearer_token(credentials)
        self.assertEqual(token1, "first_token")

        self.vault_client.update_config({"new_key": "new_value"})

        token2 = self.vault_client.get_bearer_token(credentials)
        self.assertEqual(token2, "second_token")
        self.assertEqual(mock_generate_bearer_token.call_count, 2)

    @patch("skyflow.vault.client.client.is_expired")
    @patch("skyflow.vault.client.client.generate_bearer_token_from_creds")
    @patch("skyflow.vault.client.client.log_info")
    def test_get_bearer_token_with_credentials_string(self, mock_log_info, mock_generate_bearer_token_from_creds, mock_is_expired):
        """Test get_bearer_token with credentials_string."""
        credentials = {"credentials_string": '{"clientID": "test", "clientName": "test"}'}
        mock_generate_bearer_token_from_creds.return_value = ("token_from_creds", None)
        mock_is_expired.return_value = False

        token = self.vault_client.get_bearer_token(credentials)

        self.assertEqual(token, "token_from_creds")
        mock_generate_bearer_token_from_creds.assert_called_once()
        mock_log_info.assert_called_with(
            SkyflowMessages.Info.GENERATE_BEARER_TOKEN_FROM_CREDENTIALS_STRING_TRIGGERED.value,
            None
        )
