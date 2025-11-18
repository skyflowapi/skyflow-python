from collections import OrderedDict
from skyflow import LogLevel
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.utils.logger import log_info, Logger
from skyflow.utils.validations import validate_vault_config, validate_connection_config, validate_update_vault_config, \
    validate_update_connection_config, validate_credentials, validate_log_level
from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import Vault
from skyflow.vault.controller import Connection
from skyflow.vault.controller import Detect

class Skyflow:
    def __init__(self, builder):
        self.__builder = builder
        log_info(SkyflowMessages.Info.CLIENT_INITIALIZED.value, self.__builder.get_logger())

    @staticmethod
    def builder():
        return Skyflow.Builder()

    def add_vault_config(self, config):
        self.__builder._Builder__add_vault_config(config)
        return self

    def remove_vault_config(self, vault_id):
        self.__builder.remove_vault_config(vault_id)

    def update_vault_config(self,config):
        self.__builder.update_vault_config(config)

    def get_vault_config(self, vault_id):
        return self.__builder.get_vault_config(vault_id).get("vault_client").get_config()

    def add_connection_config(self, config):
        self.__builder._Builder__add_connection_config(config)
        return self

    def remove_connection_config(self, connection_id):
        self.__builder.remove_connection_config(connection_id)
        return self

    def update_connection_config(self, config):
        self.__builder.update_connection_config(config)
        return self

    def get_connection_config(self, connection_id):
        return self.__builder.get_connection_config(connection_id).get("vault_client").get_config()

    def add_skyflow_credentials(self, credentials):
        self.__builder._Builder__add_skyflow_credentials(credentials)
        return self

    def update_skyflow_credentials(self, credentials):
        self.__builder._Builder__add_skyflow_credentials(credentials)

    def set_log_level(self, log_level):
        self.__builder._Builder__set_log_level(log_level)
        return self

    def get_log_level(self):
        return self.__builder._Builder__log_level

    def update_log_level(self, log_level):
        self.__builder._Builder__set_log_level(log_level)

    def vault(self, vault_id = None) -> Vault:
        vault_config = self.__builder.get_vault_config(vault_id)
        return vault_config.get("vault_controller")

    def connection(self, connection_id = None) -> Connection:
        connection_config = self.__builder.get_connection_config(connection_id)
        return connection_config.get("controller")
    
    def detect(self, vault_id = None) -> Detect:
        vault_config = self.__builder.get_vault_config(vault_id)
        return vault_config.get("detect_controller")

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
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )
            if vault_id in [vault.get("vault_id") for vault in self.__vault_list]:
                log_info(SkyflowMessages.Info.VAULT_CONFIG_EXISTS.value.format(vault_id), self.__logger)
                raise SkyflowError(
                    SkyflowMessages.Error.VAULT_ID_ALREADY_EXISTS.value.format(vault_id),
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )

            self.__vault_list.append(config)
            return self

        def remove_vault_config(self, vault_id):
            if vault_id in self.__vault_configs.keys():
                self.__vault_configs.pop(vault_id)
            else:
                raise SkyflowError(SkyflowMessages.Error.INVALID_VAULT_ID.value,
                          SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

        def update_vault_config(self, config):
            validate_update_vault_config(self.__logger, config)
            vault_id = config.get("vault_id")
            vault_config = self.__vault_configs[vault_id]
            vault_config.get("vault_client").update_config(config)

        def get_vault_config(self, vault_id):
            if vault_id is None:
                if self.__vault_configs:
                    return next(iter(self.__vault_configs.values()))
                raise SkyflowError(SkyflowMessages.Error.EMPTY_VAULT_CONFIGS.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

            if vault_id in self.__vault_configs:
                return self.__vault_configs.get(vault_id)
            log_info(SkyflowMessages.Info.VAULT_CONFIG_DOES_NOT_EXIST.value.format(vault_id), self.__logger)
            raise SkyflowError(SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(vault_id), SkyflowMessages.ErrorCodes.INVALID_INPUT.value)


        def add_connection_config(self, config):
            connection_id = config.get("connection_id")
            if not isinstance(connection_id, str) or not connection_id:
                raise SkyflowError(
                    SkyflowMessages.Error.INVALID_CONNECTION_ID.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )
            if connection_id in [connection.get("connection_id") for connection in self.__connection_list]:
                log_info(SkyflowMessages.Info.CONNECTION_CONFIG_EXISTS.value.format(connection_id), self.__logger)
                raise SkyflowError(
                    SkyflowMessages.Error.CONNECTION_ID_ALREADY_EXISTS.value.format(connection_id),
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )
            self.__connection_list.append(config)
            return self

        def remove_connection_config(self, connection_id):
            if connection_id in self.__connection_configs.keys():
                self.__connection_configs.pop(connection_id)
            else:
                raise SkyflowError(SkyflowMessages.Error.INVALID_CONNECTION_ID.value,
                          SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

        def update_connection_config(self, config):
            validate_update_connection_config(self.__logger, config)
            connection_id = config['connection_id']
            connection_config = self.__connection_configs[connection_id]
            connection_config.get("vault_client").update_config(config)

        def get_connection_config(self, connection_id):
            if connection_id is None:
                if self.__connection_configs:
                    return next(iter(self.__connection_configs.values()))

                raise SkyflowError(SkyflowMessages.Error.EMPTY_CONNECTION_CONFIGS.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

            if connection_id in self.__connection_configs:
                return self.__connection_configs.get(connection_id)
            log_info(SkyflowMessages.Info.CONNECTION_CONFIG_DOES_NOT_EXIST.value.format(connection_id), self.__logger)
            raise SkyflowError(SkyflowMessages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format(connection_id), SkyflowMessages.ErrorCodes.INVALID_INPUT.value)


        def add_skyflow_credentials(self, credentials):
            self.__skyflow_credentials = credentials
            return self

        def set_log_level(self, log_level):
            self.__log_level = log_level
            return self

        def get_logger(self):
            return self.__logger

        def __add_vault_config(self, config):
            validate_vault_config(self.__logger, config)
            vault_id = config.get("vault_id")
            vault_client = VaultClient(config)
            self.__vault_configs[vault_id] = {
                "vault_client": vault_client,
                "vault_controller": Vault(vault_client),
                "detect_controller": Detect(vault_client)
            }
            log_info(SkyflowMessages.Info.VAULT_CONTROLLER_INITIALIZED.value.format(config.get("vault_id")), self.__logger)
            log_info(SkyflowMessages.Info.DETECT_CONTROLLER_INITIALIZED.value.format(config.get("vault_id")), self.__logger)

        def __add_connection_config(self, config):
            validate_connection_config(self.__logger, config)
            connection_id = config.get("connection_id")
            vault_client = VaultClient(config)
            self.__connection_configs[connection_id] = {
                "vault_client": vault_client,
                "controller": Connection(vault_client)
            }
            log_info(SkyflowMessages.Info.CONNECTION_CONTROLLER_INITIALIZED.value.format(config.get("connection_id")), self.__logger)

        def __update_vault_client_logger(self, log_level, logger):
            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get("vault_client").set_logger(log_level,logger)

            for connection_id, connection_config in self.__connection_configs.items():
                connection_config.get("vault_client").set_logger(log_level,logger)

        def __set_log_level(self, log_level):
            validate_log_level(self.__logger, log_level)
            self.__log_level = log_level
            self.__logger.set_log_level(log_level)
            self.__update_vault_client_logger(log_level, self.__logger)
            log_info(SkyflowMessages.Info.LOGGER_SETUP_DONE.value, self.__logger)
            log_info(SkyflowMessages.Info.CURRENT_LOG_LEVEL.value.format(self.__log_level), self.__logger)

        def __add_skyflow_credentials(self, credentials):
            if credentials is not None:
                self.__skyflow_credentials = credentials
                validate_credentials(self.__logger, credentials)
                for vault_id, vault_config in self.__vault_configs.items():
                    vault_config.get("vault_client").set_common_skyflow_credentials(credentials)

                for connection_id, connection_config in self.__connection_configs.items():
                    connection_config.get("vault_client").set_common_skyflow_credentials(self.__skyflow_credentials)
        def build(self):
            validate_log_level(self.__logger, self.__log_level)
            self.__logger.set_log_level(self.__log_level)

            for config in self.__vault_list:
                self.__add_vault_config(config)

            for config in self.__connection_list:
                self.__add_connection_config(config)

            self.__update_vault_client_logger(self.__log_level, self.__logger)

            self.__add_skyflow_credentials(self.__skyflow_credentials)

            return Skyflow(self)
