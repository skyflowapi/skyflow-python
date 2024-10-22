from collections import OrderedDict
from skyflow import LogLevel
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.utils.logger import log_info, Logger, log_error
from skyflow.utils.validations import validate_vault_config, validate_connection_config, validate_update_vault_config, \
    validate_update_connection_config, validate_credentials, validate_log_level
from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import Vault
from skyflow.vault.controller import Connection

class Skyflow:
    def __init__(self, builder):
        self.__builder = builder
        log_info(SkyflowMessages.Info.CLIENT_INITIALIZED.value,
                 SkyflowMessages.InterfaceName.CLIENT.value,
                 self.__builder.get_logger())

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
            self.__vault_list = list()
            self.__connection_configs = OrderedDict()
            self.__connection_list = list()
            self.__skyflow_credentials = None
            self.__log_level = LogLevel.ERROR
            self.__logger = Logger(LogLevel.ERROR)

        def add_vault_config(self, config):
            vault_id = config.get("vault_id")
            if not isinstance(vault_id, str) or not vault_id:
                raise SkyflowError(
                    SkyflowMessages.Error.INVALID_VAULT_ID.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                    logger=self.__logger
                )
            if vault_id in [vault.get("vault_id") for vault in self.__vault_list]:
                raise SkyflowError(
                    SkyflowMessages.Error.VAULT_ID_ALREADY_EXISTS.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                    logger=self.__logger
                )

            self.__vault_list.append(config)
            return self

        def remove_vault_config(self, vault_id):
            if vault_id in self.__vault_configs.keys():
                self.__vault_configs.pop(vault_id)
            else:
                log_error(SkyflowMessages.Error.INVALID_VAULT_ID.value,
                          SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                          logger = self.__logger)

        def update_vault_config(self, config):
            validate_update_vault_config(self.__logger, config)
            vault_id = config.get("vault_id")
            vault_config = self.__vault_configs[vault_id]
            vault_config.get("vault_client").update_config(config)

        def get_vault_config(self, vault_id):
            if vault_id is None:
                if self.__vault_configs:
                    return next(iter(self.__vault_configs.values()))
                raise SkyflowError(SkyflowMessages.Error.EMPTY_VAULT_CONFIGS.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value, logger = self.__logger)

            if vault_id in self.__vault_configs:
                return self.__vault_configs.get(vault_id)
            raise SkyflowError(SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(vault_id), SkyflowMessages.ErrorCodes.INVALID_INPUT.value, logger = self.__logger)

        def add_connection_config(self, config):
            connection_id = config.get("connection_id")
            if not isinstance(connection_id, str) or not connection_id:
                raise SkyflowError(
                    SkyflowMessages.Error.INVALID_CONNECTION_ID.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                    logger = self.__logger
                )
            if connection_id in [connection.get("connection_id") for connection in self.__connection_list]:
                raise SkyflowError(
                    SkyflowMessages.Error.CONNECTION_ID_ALREADY_EXISTS.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                    logger=self.__logger
                )
            self.__connection_list.append(config)
            return self

        def remove_connection_config(self, connection_id):
            if connection_id in self.__connection_configs.keys():
                self.__connection_configs.pop(connection_id)
            else:
                log_error(SkyflowMessages.Error.INVALID_CONNECTION_ID.value,
                          SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
                          logger = self.__logger)

        def update_connection_config(self, config):
            validate_update_connection_config(self.__logger, config)
            connection_id = config['connection_id']
            connection_config = self.__connection_configs[connection_id]
            connection_config.get("vault_client").update_config(config)

        def get_connection_config(self, connection_id):
            if connection_id is None:
                if self.__connection_configs:
                    return next(iter(self.__connection_configs.values()))
                return SkyflowError(SkyflowMessages.Error.EMPTY_CONNECTION_CONFIGS, SkyflowMessages.ErrorCodes.INVALID_INPUT.value, logger = self.__logger)

            if connection_id in self.__connection_configs:
                return self.__connection_configs.get(connection_id)
            raise SkyflowError(SkyflowMessages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format(connection_id), SkyflowMessages.ErrorCodes.INVALID_INPUT.value, logger = self.__logger)

        def add_skyflow_credentials(self, credentials):
            self.__skyflow_credentials = credentials
            return self

        def set_log_level(self, log_level):
            self.__log_level = log_level
            return self

        def get_logger(self):
            return self.__logger

        def build(self):
            log_info(SkyflowMessages.Info.INITIALIZE_CLIENT.value, SkyflowMessages.InterfaceName.CLIENT.value, self.__logger)
            validate_log_level(self.__logger, self.__log_level)
            self.__logger.set_log_level(self.__log_level)

            for config in self.__vault_list:
                validate_vault_config(self.__logger, config)
                vault_id = config.get("vault_id")
                vault_client = VaultClient(config)
                self.__vault_configs[vault_id] = {
                    "vault_client": vault_client,
                    "controller": Vault(vault_client)
                }

            for config in self.__connection_list:
                validate_connection_config(self.__logger, config=config)
                connection_id = config.get("connection_id")
                vault_client = VaultClient(config)
                self.__connection_configs[connection_id] = {
                    "vault_client": vault_client,
                    "controller": Connection(vault_client)
                }

            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get("vault_client").set_logger(self.__log_level, self.__logger)

            for connection_id, connection_config in self.__connection_configs.items():
                connection_config.get("vault_client").set_logger(self.__log_level, self.__logger)

            if self.__skyflow_credentials is not None:
                validate_credentials(self.__logger, self.__skyflow_credentials)
                for vault_id, vault_config in self.__vault_configs.items():
                    vault_config.get("vault_client").set_common_skyflow_credentials(self.__skyflow_credentials)

                for connection_id, connection_config in self.__connection_configs.items():
                    connection_config.get("vault_client").set_common_skyflow_credentials(self.__skyflow_credentials)

            return Skyflow(self)
