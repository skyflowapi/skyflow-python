import unittest
from unittest.mock import patch

from common.errors import SkyflowError
from common.utils import LogLevel, Env
from skyflow.client import Skyflow

VALID_VAULT_CONFIG = {
    "vault_id": "VAULT_ID",
    "cluster_id": "CLUSTER_ID",
    "env": Env.DEV,
    "credentials": {"path": "/path/to/valid_credentials.json"},
}

INVALID_VAULT_CONFIG = {
    "cluster_id": "CLUSTER_ID",  # missing vault_id
    "env": Env.DEV,
    "credentials": {"path": "/path/to/valid_credentials.json"},
}

VALID_CREDENTIALS = {"path": "/path/to/valid_credentials.json"}


class TestSkyflowVaultConfig(unittest.TestCase):
    """v2 parity: flowvault gained remove_vault_config/update_vault_config/
    update_skyflow_credentials/update_log_level/get_log_level via the shared common base --
    these confirm they actually work here too, not just on v2."""

    def setUp(self):
        self.builder = Skyflow.builder()

    def test_add_vault_config_success(self):
        builder = self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.assertEqual(builder, self.builder)

    def test_add_vault_config_invalid_raises(self):
        with self.assertRaises(SkyflowError):
            self.builder.add_vault_config(INVALID_VAULT_CONFIG)

    def test_build_and_get_vault_config(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        config = client.get_vault_config("VAULT_ID")
        self.assertEqual(config.get("vault_id"), "VAULT_ID")

    @patch("skyflow.vault.client.client.VaultClient.update_config")
    def test_update_vault_config(self, mock_update_config):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        updated = dict(VALID_VAULT_CONFIG)
        updated["cluster_id"] = "NEW_CLUSTER"
        client.update_vault_config(updated)
        mock_update_config.assert_called_once()

    def test_update_vault_config_with_invalid_vault_id_raises(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        invalid = dict(VALID_VAULT_CONFIG)
        invalid["vault_id"] = "does_not_exist"
        with self.assertRaises(SkyflowError):
            client.update_vault_config(invalid)

    def test_remove_vault_config(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        client.remove_vault_config("VAULT_ID")
        with self.assertRaises(SkyflowError):
            client.get_vault_config("VAULT_ID")

    def test_add_and_update_skyflow_credentials(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        client.add_skyflow_credentials(VALID_CREDENTIALS)
        new_credentials = {"path": "/path/to/other_credentials.json"}
        client.update_skyflow_credentials(new_credentials)
        # no assertion error means both went through the same underlying builder path

    def test_set_and_get_log_level(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        client.set_log_level(LogLevel.INFO)
        self.assertEqual(client.get_log_level(), LogLevel.INFO)

    def test_update_log_level_delegates_to_set_log_level(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        client.update_log_level(LogLevel.INFO)
        self.assertEqual(client.get_log_level(), LogLevel.INFO)

    @patch("common.client.base_skyflow.log_warn")
    def test_update_log_level_emits_deprecation_warning(self, mock_warn):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        client.update_log_level(LogLevel.INFO)
        mock_warn.assert_called_once()
        self.assertIn("set_log_level", mock_warn.call_args[0][0])

    def test_vault_returns_vault_controller(self):
        client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        vault = client.vault("VAULT_ID")
        self.assertTrue(hasattr(vault, "insert"))


class TestConnectionAndDetectNotSupported(unittest.TestCase):
    """flowvault has no Connection/Detect concept this round -- ConnectionMixin/DetectMixin are
    only added to a variant's produced Skyflow class when connection_cls/detect_cls are supplied,
    so these methods are genuinely absent here (AttributeError), unlike v2 where they work."""

    def setUp(self):
        self.client = Skyflow.builder().add_vault_config(VALID_VAULT_CONFIG).build()

    def test_connection_raises(self):
        with self.assertRaises(AttributeError):
            self.client.connection()

    def test_detect_raises(self):
        with self.assertRaises(AttributeError):
            self.client.detect()

    def test_add_connection_config_raises(self):
        with self.assertRaises(AttributeError):
            self.client.add_connection_config({})

    def test_remove_connection_config_raises(self):
        with self.assertRaises(AttributeError):
            self.client.remove_connection_config("x")

    def test_update_connection_config_raises(self):
        with self.assertRaises(AttributeError):
            self.client.update_connection_config({})

    def test_get_connection_config_raises(self):
        with self.assertRaises(AttributeError):
            self.client.get_connection_config("x")


if __name__ == "__main__":
    unittest.main()
