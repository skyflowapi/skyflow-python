from collections import OrderedDict
from skyflow import LogLevel
from skyflow.error import SkyflowError
from skyflow.utils.validations import validate_vault_config, validate_connection_config
from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import Vault
from skyflow.vault.controller import Connection

class Skyflow:
    def __init__(self, builder):
        self.__builder = builder

    @staticmethod
    def builder():
        return Skyflow.Builder()

    def add_vault_config(self, config):
        self.__builder.add_vault_config(config)
        return self

    def remove_vault_config(self, vault_id):
        self.__builder.remove_vault_config(vault_id)
        return self

    def update_vault_config(self,config):
        self.__builder.update_vault_config(config)
        return self

    def get_vault_config(self, vault_id):
        return self.__builder.get_vault_config(vault_id)

    def add_connection_config(self, config):
        self.__builder.add_connection_config(config)
        return self

    def remove_connection_config(self, connection_id):
        self.__builder.remove_connection_config(connection_id)
        return self

    def update_connection_config(self, config):
        self.__builder.update_connection_config(config)
        return self

    def get_connection_config(self, connection_id):
        self.__builder.get_connection_config(connection_id)
        return self

    def add_skyflow_credentials(self, credentials):
        self.__builder.add_skyflow_credentials(credentials)
        return self

    def update_skyflow_credentials(self, credentials):
        self.__builder.add_skyflow_credentials(credentials)
        return self

    def set_log_level(self, log_level):
        self.__builder.set_log_level(log_level)
        return self

    def update_log_level(self, log_level):
        self.__builder.set_log_level(log_level)
        return self

    def vault(self, vault_id = None):
        vault_config = self.__builder.get_vault_config(vault_id)
        return vault_config.get("controller")

    def connection(self, connection_id = None):
        connection_config = self.__builder.get_connection_config(connection_id)
        return connection_config.get("controller")

    class Builder:
        def __init__(self):
            self.__vault_configs = OrderedDict()
            self.__connection_configs = OrderedDict()
            self.__skyflow_credentials = None
            self.__log_level = LogLevel.ERROR

        def add_vault_config(self, config):
            if validate_vault_config(config) and config.get("vault_id") not in self.__vault_configs.keys():
                vault_id = config.get("vault_id")
                vault_client = VaultClient(config)
                self.__vault_configs[vault_id] = {
                    "vault_client": vault_client,
                    "controller": Vault(vault_client)
                }
                return self
            else:
                raise SkyflowError(f"Vault config with id {config['vault_id']} already exists")

        def remove_vault_config(self, vault_id):
            if vault_id in self.__vault_configs.keys():
                self.__vault_configs.pop(vault_id)
            else:
                raise SkyflowError(f"Vault config with id {vault_id} not found")

        def update_vault_config(self, config):
            vault_id = config.get("vault_id")
            if not vault_id:
                raise SkyflowError("vault_id is required and cannot be None")
            if vault_id in self.__vault_configs.keys():
                vault_config = self.__vault_configs[vault_id]
                vault_config.get("vault_client").update_config(config)
            else:
                raise SkyflowError(f"Vault config with id {vault_id} not found")

        def get_vault_config(self, vault_id):
            if vault_id in self.__vault_configs.keys():
                vault_config = self.__vault_configs.get(vault_id)
                return vault_config
            raise SkyflowError(f"Vault config with id {vault_id} not found")

        def add_connection_config(self, config):
            if validate_connection_config(config) and config["connection_id"] not in self.__connection_configs.keys():
                connection_id = config.get("connection_id")
                vault_client = VaultClient(config)
                self.__connection_configs[connection_id] = {
                    "vault_client": vault_client,
                    "controller": Connection(vault_client)
                }
                return self
            else:
                raise SkyflowError(f"Connection config with id {config['connection_id']} already exists")

        def remove_connection_config(self, connection_id):
            if connection_id in self.__connection_configs.keys():
                self.__connection_configs.pop(connection_id)
            else:
                raise SkyflowError(f"Connection config with id {connection_id} not found")

        def update_connection_config(self, config):
            connection_id = config['connection_id']
            if not connection_id:
                raise SkyflowError("connection_id is required and can not be empty")

            if connection_id in self.__connection_configs.keys():
                connection_config = self.__connection_configs[connection_id]
                connection_config.get("vault_client").update_config(config)
            else:
                raise SkyflowError(f"Connection config with id {connection_id} not found")

        def get_connection_config(self, connection_id):
            if connection_id in self.__connection_configs.keys():
                connection_config = self.__connection_configs[connection_id]
                return connection_config
            raise SkyflowError(f"Connection config with id {connection_id} not found")

        def add_skyflow_credentials(self, credentials):
            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get("vault_client").set_common_skyflow_credentials(credentials)

            for connection_id, connection_config in self.__connection_configs.items():
                connection_config.get("vault_client").set_common_skyflow_credentials(credentials)
            return self

        def set_log_level(self, log_level):
            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get("vault_client").set_log_level(log_level)

            for connection_id, connection_config in self.__connection_configs.items():
                connection_config.get("vault_client").set_log_level(log_level)
            return self

        def build(self):
            return Skyflow(self)