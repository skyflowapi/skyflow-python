from v2.skyflow.error import SkyflowError
from v2.skyflow.utils import LogLevel, is_value_in_enum
from v2.skyflow.utils.validations import validate_config


class Builder:
    def __init__(self):
        self.__vault_configs =  {}
        self.__connection_configs =  {}
        self.__skyflow_credentials = None
        self.__log_level = LogLevel.ERROR

    def add_vault_config(self, config):
        if validate_config(config) and config["vault_id"] not in self.__vault_configs.keys():
            vault_id = config.get("vault_id")
            self.__vault_configs[vault_id] = config
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
            self.__vault_configs[vault_id] = config
        else:
            raise SkyflowError(f"Vault config with id {vault_id} not found")

    def get_vault_config(self, vault_id):
        if vault_id in self.__vault_configs.keys():
            return self.__vault_configs[vault_id]
        raise SkyflowError(f"Vault config with id {vault_id} not found")

    def add_connection_config(self, config):
        if validate_config(config) and config["connection_id"] not in self.__connection_configs.keys():
            connection_id = config.get("connection_id")
            self.__connection_configs[connection_id] = config
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
            self.__connection_configs[connection_id] = config
        else:
            raise SkyflowError(f"Connection config with id {connection_id} not found")


    def get_connection_config(self, connection_id):
        if connection_id in self.__connection_configs.keys():
            return self.__connection_configs[connection_id]
        raise SkyflowError(f"Connection config with id {connection_id} not found")

    def add_skyflow_credentials(self, credentials):
        self.__skyflow_credentials = credentials
        return self

    def get_skyflow_credentials(self):
        if self.__skyflow_credentials is not None:
            return self.__skyflow_credentials
        else:
            raise SkyflowError(f"Skyflow credentials are now found")

    def set_log_level(self, log_level):
        self.__log_level = log_level
        return self

    def get_log_level(self):
        return self.__log_level

    def vault(self, vault_id):
        #return vault controller
        pass

    def build(self):
        from v2.skyflow.client import Skyflow
        return Skyflow(self)
