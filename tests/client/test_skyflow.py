import unittest
from unittest.mock import  patch

from skyflow import LogLevel, Env
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow import Skyflow
from tests.constants.test_constants import VALID_VAULT_CONFIG, INVALID_VAULT_CONFIG, VALID_CONNECTION_CONFIG, \
    INVALID_CONNECTION_CONFIG, VALID_CREDENTIALS


class TestSkyflow(unittest.TestCase):

    def setUp(self):
        self.builder = Skyflow.builder()

    def test_add_vault_config_success(self):
        builder = self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.assertIn(VALID_VAULT_CONFIG, self.builder._Builder__vault_list)
        self.assertEqual(builder, self.builder)

    def test_add_already_exists_vault_config(self):
        builder = self.builder.add_vault_config(VALID_VAULT_CONFIG)
        with self.assertRaises(SkyflowError) as context:
            builder.add_vault_config(VALID_VAULT_CONFIG)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.VAULT_ID_ALREADY_EXISTS.value.format(VALID_VAULT_CONFIG.get("vault_id")))


    def test_add_vault_config_invalid(self):
        with self.assertRaises(SkyflowError) as context:
            self.builder.add_vault_config(INVALID_VAULT_CONFIG)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_VAULT_ID.value)

    def test_remove_vault_config_valid(self):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        result = self.builder.remove_vault_config(VALID_VAULT_CONFIG['vault_id'])

        self.assertNotIn(VALID_VAULT_CONFIG['vault_id'], self.builder._Builder__vault_configs)

    @patch('skyflow.client.skyflow.log_error')
    def test_remove_vault_config_invalid(self, mock_log_error):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        self.builder.remove_vault_config("invalid_id")
        mock_log_error.assert_called_once()


    @patch('skyflow.vault.client.client.VaultClient.update_config')
    def test_update_vault_config_valid(self, mock_validate):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        updated_config = VALID_VAULT_CONFIG.copy()
        updated_config["cluster_id"] = "sb.area52"
        self.builder.update_vault_config(updated_config)
        mock_validate.assert_called_once()

    def test_get_vault(self):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()

        config = self.builder.get_vault_config(VALID_VAULT_CONFIG["vault_id"])

        self.assertEqual(self.builder._Builder__vault_list[0], VALID_VAULT_CONFIG)

    def test_get_vault_with_vault_id_none(self):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        vault  = self.builder.get_vault_config(None)
        config = vault.get("vault_client").get_config()
        self.assertEqual(self.builder._Builder__vault_list[0], config)

    def test_get_vault_with_empty_vault_list_when_vault_id_is_none_raises_error(self):
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_vault_config(None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_VAULT_CONFIGS.value)

    def test_get_vault_with_invalid_vault_id_raises_error(self):
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_vault_config('invalid_id')
        self.assertEqual(context.exception.message, SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format('invalid_id'))

    def test_get_vault_with_invalid_vault_id_and_non_empty_list_raises_error(self):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_vault_config('invalid_vault_id')

        self.assertEqual(context.exception.message, SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format("invalid_vault_id"))


    @patch('skyflow.client.skyflow.validate_vault_config')
    def test_build_calls_validate_vault_config(self, mock_validate_vault_config):
        self.builder.add_vault_config(VALID_VAULT_CONFIG)
        self.builder.build()
        mock_validate_vault_config.assert_called_once_with(self.builder._Builder__logger, VALID_VAULT_CONFIG)

    def test_add_connection_config_valid(self):
        result = self.builder.add_connection_config(VALID_CONNECTION_CONFIG)

        self.assertIn(VALID_CONNECTION_CONFIG, self.builder._Builder__connection_list)
        self.assertEqual(result, self.builder)

    def test_add_already_exists_connection_config(self):
        connection_id = VALID_CONNECTION_CONFIG.get("connection_id")
        builder = self.builder.add_connection_config(VALID_CONNECTION_CONFIG)

        with self.assertRaises(SkyflowError) as context:
            builder.add_connection_config(VALID_CONNECTION_CONFIG)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.CONNECTION_ID_ALREADY_EXISTS.value.format(connection_id))

    def test_add_connection_config_invalid(self):
        with self.assertRaises(SkyflowError) as context:
            self.builder.add_connection_config(INVALID_CONNECTION_CONFIG)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CONNECTION_ID.value)

    def test_remove_connection_config_valid(self):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        result = self.builder.remove_connection_config(VALID_CONNECTION_CONFIG.get("connection_id"))

        self.assertNotIn(VALID_CONNECTION_CONFIG.get("connection_id"), self.builder._Builder__connection_configs)


    @patch('skyflow.client.skyflow.log_error')
    def test_remove_connection_config_invalid(self, mock_log_error):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        self.builder.remove_connection_config("invalid_id")
        mock_log_error.assert_called_once()

    @patch('skyflow.vault.client.client.VaultClient.update_config')
    def test_update_connection_config_valid(self, mock_validate):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        updated_config = VALID_CONNECTION_CONFIG.copy()
        updated_config["connection_url"] = "test_url"
        self.builder.update_connection_config(updated_config)
        mock_validate.assert_called_once()

    def test_get_connection_config(self):
        connection_id = VALID_CONNECTION_CONFIG.get("connection_id")
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()

        connection = self.builder.get_connection_config(connection_id)
        config = connection.get("vault_client").get_config()
        self.assertEqual(self.builder._Builder__connection_list[0], config)

    def test_get_connection_config_with_connection_id_none(self):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        self.builder.get_connection_config(None)
        self.assertEqual(self.builder._Builder__connection_list[0], VALID_CONNECTION_CONFIG)

    def test_get_connection_with_empty_connection_list_raises_error(self):
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_connection_config('invalid_id')
        self.assertEqual(context.exception.message, SkyflowMessages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format('invalid_id'))

    def test_get_connection_with_invalid_connection_id_raises_error(self):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_connection_config('invalid_connection_id')

        self.assertEqual(context.exception.message, SkyflowMessages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format('invalid_connection_id'))

    def test_get_connection_with_invalid_connection_id_and_empty_list_raises_Error(self):
        self.builder.build()
        with self.assertRaises(SkyflowError) as context:
            self.builder.get_connection_config(None)

        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_CONNECTION_CONFIGS.value)

    @patch('skyflow.client.skyflow.validate_connection_config')
    def test_build_calls_validate_connection_config(self, mock_validate):
        self.builder.add_connection_config(VALID_CONNECTION_CONFIG)
        self.builder.build()
        mock_validate.assert_called_once_with(self.builder._Builder__logger, VALID_CONNECTION_CONFIG)


    def test_build_valid(self):
        self.builder.add_vault_config(VALID_VAULT_CONFIG).add_connection_config(VALID_CONNECTION_CONFIG)
        client = self.builder.build()
        self.assertIsInstance(client, Skyflow)

    def test_set_log_level(self):
        self.builder.set_log_level(LogLevel.INFO)
        self.assertEqual(self.builder._Builder__log_level, LogLevel.INFO)

    def test_invalid_credentials(self):
        builder = self.builder.add_skyflow_credentials(VALID_CREDENTIALS)
        builder.add_connection_config(VALID_CONNECTION_CONFIG)
        builder.add_vault_config(VALID_VAULT_CONFIG)
        builder.build()
        self.assertEqual(VALID_CREDENTIALS, self.builder._Builder__skyflow_credentials)
        self.assertEqual(builder, self.builder)

    @patch('skyflow.client.skyflow.validate_vault_config')
    def test_skyflow_client_add_remove_vault_config(self, mock_validate_vault_config):
        skyflow_client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        new_config = VALID_VAULT_CONFIG.copy()
        new_config['vault_id'] = "d3dd9bbb7abc4c779b72f32cb7ee5d12"
        skyflow_client.add_vault_config(new_config)

        assert mock_validate_vault_config.call_count == 2

        self.assertEqual("d3dd9bbb7abc4c779b72f32cb7ee5d12",
                         skyflow_client.get_vault_config(new_config['vault_id']).get("vault_id"))

        skyflow_client.remove_vault_config(new_config['vault_id'])
        with self.assertRaises(SkyflowError) as context:
            skyflow_client.get_vault_config(new_config['vault_id']).get("vault_id")

        self.assertEqual(context.exception.message, SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(
            new_config['vault_id']))

    @patch('skyflow.vault.client.client.VaultClient.update_config')
    def test_skyflow_client_update_and_get_vault_config(self, mock_update_config):
        skyflow_client = self.builder.add_vault_config(VALID_VAULT_CONFIG).build()
        new_config = VALID_VAULT_CONFIG.copy()
        new_config['env'] = Env.SANDBOX
        skyflow_client.update_vault_config(new_config)
        mock_update_config.assert_called_once()

        vault = skyflow_client.get_vault_config(VALID_VAULT_CONFIG.get("vault_id"))

        self.assertEqual(VALID_VAULT_CONFIG.get("vault_id"), vault.get("vault_id"))

    @patch('skyflow.client.skyflow.validate_connection_config')
    def test_skyflow_client_add_remove_connection_config(self, mock_validate_connection_config):
        skyflow_client = self.builder.add_connection_config(VALID_CONNECTION_CONFIG).build()
        new_config = VALID_CONNECTION_CONFIG.copy()
        new_config['connection_id'] = "ef34fc6b0b914ad59a1754c06f10b243"
        skyflow_client.add_connection_config(new_config)

        assert mock_validate_connection_config.call_count == 2
        self.assertEqual("ef34fc6b0b914ad59a1754c06f10b243", skyflow_client.get_connection_config(new_config['connection_id']).get("connection_id"))

        skyflow_client.remove_connection_config("ef34fc6b0b914ad59a1754c06f10b243")
        with self.assertRaises(SkyflowError) as context:
            skyflow_client.get_connection_config(new_config['connection_id']).get("connection_id")

        self.assertEqual(context.exception.message, SkyflowMessages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format(new_config['connection_id']))


    @patch('skyflow.vault.client.client.VaultClient.update_config')
    def test_skyflow_client_update_and_get_connection_config(self, mock_update_config):
        builder = self.builder
        skyflow_client = builder.add_connection_config(VALID_CONNECTION_CONFIG).build()
        new_config = VALID_CONNECTION_CONFIG.copy()
        new_config['connection_url'] = 'updated_url'
        skyflow_client.update_connection_config(new_config)
        mock_update_config.assert_called_once()

        connection = skyflow_client.get_connection_config(VALID_CONNECTION_CONFIG.get("connection_id"))

        self.assertEqual(VALID_CONNECTION_CONFIG.get("connection_id"), connection.get("connection_id"))

    def test_skyflow_add_and_update_skyflow_credentials(self):
        builder = self.builder
        skyflow_client = builder.add_connection_config(VALID_CONNECTION_CONFIG).build()
        skyflow_client.add_skyflow_credentials(VALID_CREDENTIALS)

        self.assertEqual(VALID_CREDENTIALS, builder._Builder__skyflow_credentials)

        new_credentials = VALID_CREDENTIALS.copy()
        new_credentials['path'] = 'path/to/new_credentials'

        skyflow_client.update_skyflow_credentials(new_credentials)

        self.assertEqual(new_credentials, builder._Builder__skyflow_credentials)


    def test_skyflow_add_and_update_log_level(self):
        builder = self.builder
        skyflow_client =  builder.add_connection_config(VALID_CONNECTION_CONFIG).build()
        skyflow_client.set_log_level(LogLevel.INFO)

        self.assertEqual(LogLevel.INFO, builder._Builder__log_level)

        skyflow_client.update_log_level(LogLevel.ERROR)
        self.assertEqual(LogLevel.ERROR, builder._Builder__log_level)


    @patch('skyflow.client.Skyflow.Builder.get_vault_config')
    def test_skyflow_vault_and_connection_method(self, mock_get_vault_config):
        builder = self.builder
        skyflow_client = builder.add_connection_config(VALID_CONNECTION_CONFIG).add_vault_config(VALID_VAULT_CONFIG).build()
        skyflow_client.vault()
        skyflow_client.connection()
        mock_get_vault_config.assert_called_once()