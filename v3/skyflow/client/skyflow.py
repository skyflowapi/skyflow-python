from collections import OrderedDict

from common.errors import SkyflowError
from common.utils import LogLevel, SkyflowMessages
from common.utils.logger import log_info, Logger
from common.utils.constants import OptionField
from common.utils.validations import validate_log_level, validate_credentials
from skyflow.utils.validations import validate_vault_config
from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import FlowVaultController


class Skyflow:
    """Minimal entry-point facade for this round -- scoped to what `insert` needs (a single
    vault config, shared credentials, log level). Not full parity with v2's Builder (no
    multi-connection support, no remove/update config, no Detect controller) -- those aren't
    part of v3's scope yet."""

    def __init__(self, builder):
        self.__builder = builder
        log_info(SkyflowMessages.Info.CLIENT_INITIALIZED.value, self.__builder.get_logger())

    @staticmethod
    def builder():
        return Skyflow.Builder()

    def add_vault_config(self, config):
        self.__builder._Builder__add_vault_config(config)
        return self

    def add_skyflow_credentials(self, credentials):
        self.__builder._Builder__add_skyflow_credentials(credentials)
        return self

    def set_log_level(self, log_level):
        self.__builder._Builder__set_log_level(log_level)
        return self

    def get_vault_config(self, vault_id):
        return self.__builder.get_vault_config(vault_id).get(OptionField.VAULT_CLIENT).get_config()

    def vault(self, vault_id=None) -> FlowVaultController:
        vault_config = self.__builder.get_vault_config(vault_id)
        return vault_config.get(OptionField.VAULT_CONTROLLER)

    class Builder:
        def __init__(self):
            self.__vault_configs = OrderedDict()
            self.__vault_list = list()
            self.__skyflow_credentials = None
            self.__log_level = LogLevel.ERROR
            self.__logger = Logger(LogLevel.ERROR)

        def add_vault_config(self, config):
            vault_id = config.get(OptionField.VAULT_ID)
            if not isinstance(vault_id, str) or not vault_id:
                raise SkyflowError(
                    SkyflowMessages.Error.INVALID_VAULT_ID.value,
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )
            if vault_id in [vault.get(OptionField.VAULT_ID) for vault in self.__vault_list]:
                raise SkyflowError(
                    SkyflowMessages.Error.VAULT_ID_ALREADY_EXISTS.value.format(vault_id),
                    SkyflowMessages.ErrorCodes.INVALID_INPUT.value
                )
            self.__vault_list.append(config)
            return self

        def get_vault_config(self, vault_id):
            if vault_id is None:
                if self.__vault_configs:
                    return next(iter(self.__vault_configs.values()))
                raise SkyflowError(SkyflowMessages.Error.EMPTY_VAULT_CONFIGS.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

            if vault_id in self.__vault_configs:
                return self.__vault_configs.get(vault_id)
            raise SkyflowError(SkyflowMessages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(vault_id), SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

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
            vault_id = config.get(OptionField.VAULT_ID)
            vault_client = VaultClient(config)
            self.__vault_configs[vault_id] = {
                OptionField.VAULT_CLIENT: vault_client,
                OptionField.VAULT_CONTROLLER: FlowVaultController(vault_client),
            }
            log_info(SkyflowMessages.Info.VAULT_CONTROLLER_INITIALIZED.value.format(vault_id), self.__logger)

        def __update_vault_client_logger(self, log_level, logger):
            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get(OptionField.VAULT_CLIENT).set_logger(log_level, logger)

        def __set_log_level(self, log_level):
            validate_log_level(self.__logger, log_level)
            self.__log_level = log_level
            self.__logger.set_log_level(log_level)
            self.__update_vault_client_logger(log_level, self.__logger)

        def __add_skyflow_credentials(self, credentials):
            if credentials is not None:
                self.__skyflow_credentials = credentials
                validate_credentials(self.__logger, credentials)
                for vault_id, vault_config in self.__vault_configs.items():
                    vault_config.get(OptionField.VAULT_CLIENT).set_common_skyflow_credentials(credentials)

        def build(self):
            validate_log_level(self.__logger, self.__log_level)
            self.__logger.set_log_level(self.__log_level)

            for config in self.__vault_list:
                self.__add_vault_config(config)

            self.__update_vault_client_logger(self.__log_level, self.__logger)
            self.__add_skyflow_credentials(self.__skyflow_credentials)

            return Skyflow(self)
