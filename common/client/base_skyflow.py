from abc import ABC, abstractmethod
from collections import OrderedDict
from common.errors import SkyflowError
from common.utils import SkyflowMessages
from common.utils.logger import log_info, log_warn
from common.utils.constants import OptionField

_BUILDER_TEMPLATE_ERROR = (
    "BaseSkyflowImpl.Builder is an interface template -- build a concrete Skyflow "
    "class via make_skyflow_class() instead of using it directly. Missing: {missing}"
)
_CONNECTIONS_NOT_SUPPORTED_ERROR = "Connections are not supported by this Skyflow SDK variant"
_DETECT_NOT_SUPPORTED_ERROR = "Detect is not supported by this Skyflow SDK variant"


class BaseSkyflow(ABC):
    @classmethod
    @abstractmethod
    def builder(cls):
        raise NotImplementedError

    @abstractmethod
    def add_vault_config(self, config):
        raise NotImplementedError

    @abstractmethod
    def remove_vault_config(self, vault_id):
        raise NotImplementedError

    @abstractmethod
    def update_vault_config(self, config):
        raise NotImplementedError

    @abstractmethod
    def get_vault_config(self, vault_id):
        raise NotImplementedError

    @abstractmethod
    def add_skyflow_credentials(self, credentials):
        raise NotImplementedError

    @abstractmethod
    def update_skyflow_credentials(self, credentials):
        raise NotImplementedError

    @abstractmethod
    def set_log_level(self, log_level):
        raise NotImplementedError

    @abstractmethod
    def update_log_level(self, log_level):
        raise NotImplementedError

    @abstractmethod
    def get_log_level(self):
        raise NotImplementedError

    @abstractmethod
    def vault(self, vault_id=None):
        raise NotImplementedError


class BaseSkyflowImpl(BaseSkyflow):

    def __init__(self, builder):
        if type(self) is BaseSkyflowImpl:
            raise SkyflowError(
                SkyflowMessages.Error.BASE_SKYFLOW_INSTANTIATION_NOT_ALLOWED.value,
                SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
            )
        self.__builder = builder
        log_info(self.__builder._skyflow_messages.Info.CLIENT_INITIALIZED.value, self.__builder.get_logger())

    @classmethod
    def builder(cls):
        return cls.Builder()

    def add_vault_config(self, config):
        self.__builder._add_vault_config(config)
        return self

    def remove_vault_config(self, vault_id):
        self.__builder.remove_vault_config(vault_id)

    def update_vault_config(self, config):
        self.__builder.update_vault_config(config)

    def get_vault_config(self, vault_id):
        return self.__builder.get_vault_config(vault_id).get(OptionField.VAULT_CLIENT).get_config()

    def add_skyflow_credentials(self, credentials):
        self.__builder._add_skyflow_credentials(credentials)
        return self

    def update_skyflow_credentials(self, credentials):
        self.__builder._add_skyflow_credentials(credentials)

    def set_log_level(self, log_level):
        self.__builder._set_log_level(log_level)
        return self

    def update_log_level(self, log_level):
        """.. deprecated:: Use set_log_level() instead. Will be removed in a future release."""
        log_warn(self.__builder._skyflow_messages.Warning.UPDATE_LOG_LEVEL_DEPRECATED.value)
        return self.set_log_level(log_level)

    def get_log_level(self):
        return self.__builder.get_log_level()

    def vault(self, vault_id=None):
        vault_config = self.__builder.get_vault_config(vault_id)
        return vault_config.get(OptionField.VAULT_CONTROLLER)

    def _get_builder(self):
        return self.__builder

    class Builder(ABC):
        _vault_client_cls = None
        _vault_controller_cls = None
        _connection_cls = None
        _detect_cls = None
        _logger_cls = None
        _default_log_level = None
        _skyflow_messages = None
        _skyflow_cls = None
        _validate_vault_config = None
        _validate_update_vault_config = None
        _validate_connection_config = None
        _validate_update_connection_config = None
        _validate_log_level = None
        _validate_credentials = None
        _set_active_log_level = None

        _REQUIRED_HOOKS = (
            '_vault_client_cls', '_vault_controller_cls', '_logger_cls', '_default_log_level',
            '_skyflow_messages', '_skyflow_cls', '_validate_vault_config',
            '_validate_update_vault_config', '_validate_log_level', '_validate_credentials',
        )

        def __init__(self):
            missing = [hook for hook in self._REQUIRED_HOOKS if getattr(self, hook) is None]
            if missing:
                raise NotImplementedError(_BUILDER_TEMPLATE_ERROR.format(missing=', '.join(missing)))
            self.__vault_configs = OrderedDict()
            self.__vault_list = list()
            self.__connection_configs = OrderedDict()
            self.__connection_list = list()
            self.__skyflow_credentials = None
            self.__log_level = self._default_log_level
            self.__logger = self._logger_cls(self._default_log_level)

        def _require_connections(self):
            if self._connection_cls is None:
                raise NotImplementedError(_CONNECTIONS_NOT_SUPPORTED_ERROR)

        def _require_detect(self):
            if self._detect_cls is None:
                raise NotImplementedError(_DETECT_NOT_SUPPORTED_ERROR)

        def add_vault_config(self, config):
            vault_id = config.get(OptionField.VAULT_ID)
            if not isinstance(vault_id, str) or not vault_id:
                raise SkyflowError(
                    self._skyflow_messages.Error.INVALID_VAULT_ID.value,
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            if vault_id in [vault.get(OptionField.VAULT_ID) for vault in self.__vault_list]:
                log_info(self._skyflow_messages.Info.VAULT_CONFIG_EXISTS.value.format(vault_id), self.__logger)
                raise SkyflowError(
                    self._skyflow_messages.Error.VAULT_ID_ALREADY_EXISTS.value.format(vault_id),
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            self.__vault_list.append(config)
            return self

        def remove_vault_config(self, vault_id):
            if vault_id in self.__vault_configs.keys():
                self.__vault_configs.pop(vault_id)
            else:
                raise SkyflowError(self._skyflow_messages.Error.INVALID_VAULT_ID.value,
                          self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

        def update_vault_config(self, config):
            self._validate_update_vault_config(self.__logger, config)
            vault_id = config.get(OptionField.VAULT_ID)
            if vault_id not in self.__vault_configs:
                raise SkyflowError(self._skyflow_messages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(vault_id), self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)
            vault_config = self.__vault_configs[vault_id]
            vault_config.get(OptionField.VAULT_CLIENT).update_config(config)

        def get_vault_config(self, vault_id):
            if vault_id is None:
                if self.__vault_configs:
                    return next(iter(self.__vault_configs.values()))
                raise SkyflowError(self._skyflow_messages.Error.EMPTY_VAULT_CONFIGS.value, self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

            if vault_id in self.__vault_configs:
                return self.__vault_configs.get(vault_id)
            log_info(self._skyflow_messages.Info.VAULT_CONFIG_DOES_NOT_EXIST.value.format(vault_id), self.__logger)
            raise SkyflowError(self._skyflow_messages.Error.VAULT_ID_NOT_IN_CONFIG_LIST.value.format(vault_id), self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

        def add_connection_config(self, config):
            self._require_connections()
            connection_id = config.get(OptionField.CONNECTION_ID)
            if not isinstance(connection_id, str) or not connection_id:
                raise SkyflowError(
                    self._skyflow_messages.Error.INVALID_CONNECTION_ID.value,
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            if connection_id in [connection.get(OptionField.CONNECTION_ID) for connection in self.__connection_list]:
                log_info(self._skyflow_messages.Info.CONNECTION_CONFIG_EXISTS.value.format(connection_id), self.__logger)
                raise SkyflowError(
                    self._skyflow_messages.Error.CONNECTION_ID_ALREADY_EXISTS.value.format(connection_id),
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            self.__connection_list.append(config)
            return self

        def remove_connection_config(self, connection_id):
            self._require_connections()
            if connection_id in self.__connection_configs.keys():
                self.__connection_configs.pop(connection_id)
            else:
                raise SkyflowError(self._skyflow_messages.Error.INVALID_CONNECTION_ID.value,
                          self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

        def update_connection_config(self, config):
            self._require_connections()
            self._validate_update_connection_config(self.__logger, config)
            connection_id = config.get(OptionField.CONNECTION_ID)
            if connection_id not in self.__connection_configs:
                raise SkyflowError(self._skyflow_messages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format(connection_id), self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)
            connection_config = self.__connection_configs[connection_id]
            connection_config.get(OptionField.VAULT_CLIENT).update_config(config)

        def get_connection_config(self, connection_id):
            self._require_connections()
            if connection_id is None:
                if self.__connection_configs:
                    return next(iter(self.__connection_configs.values()))

                raise SkyflowError(self._skyflow_messages.Error.EMPTY_CONNECTION_CONFIGS.value, self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

            if connection_id in self.__connection_configs:
                return self.__connection_configs.get(connection_id)
            log_info(self._skyflow_messages.Info.CONNECTION_CONFIG_DOES_NOT_EXIST.value.format(connection_id), self.__logger)
            raise SkyflowError(self._skyflow_messages.Error.CONNECTION_ID_NOT_IN_CONFIG_LIST.value.format(connection_id), self._skyflow_messages.ErrorCodes.INVALID_INPUT.value)

        def add_skyflow_credentials(self, credentials):
            self.__skyflow_credentials = credentials
            return self

        def set_log_level(self, log_level):
            self.__log_level = log_level
            return self

        def get_logger(self):
            return self.__logger

        def get_log_level(self):
            return self.__log_level

        def _add_vault_config(self, config):
            self._validate_vault_config(self.__logger, config)
            vault_id = config.get(OptionField.VAULT_ID)
            if vault_id in self.__vault_configs:
                raise SkyflowError(
                    self._skyflow_messages.Error.VAULT_ID_ALREADY_EXISTS.value.format(vault_id),
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            vault_client = self._vault_client_cls(config)
            vault_config = {
                OptionField.VAULT_CLIENT: vault_client,
                OptionField.VAULT_CONTROLLER: self._vault_controller_cls(vault_client),
            }
            if self._detect_cls is not None:
                vault_config[OptionField.DETECT_CONTROLLER] = self._detect_cls(vault_client)
            self.__vault_configs[vault_id] = vault_config
            log_info(self._skyflow_messages.Info.VAULT_CONTROLLER_INITIALIZED.value.format(vault_id), self.__logger)
            if self._detect_cls is not None:
                log_info(self._skyflow_messages.Info.DETECT_CONTROLLER_INITIALIZED.value.format(vault_id), self.__logger)

        def _add_connection_config(self, config):
            self._validate_connection_config(self.__logger, config)
            connection_id = config.get(OptionField.CONNECTION_ID)
            if connection_id in self.__connection_configs:
                raise SkyflowError(
                    self._skyflow_messages.Error.CONNECTION_ID_ALREADY_EXISTS.value.format(connection_id),
                    self._skyflow_messages.ErrorCodes.INVALID_INPUT.value
                )
            vault_client = self._vault_client_cls(config)
            self.__connection_configs[connection_id] = {
                OptionField.VAULT_CLIENT: vault_client,
                OptionField.CONTROLLER: self._connection_cls(vault_client)
            }
            log_info(self._skyflow_messages.Info.CONNECTION_CONTROLLER_INITIALIZED.value.format(connection_id), self.__logger)

        def _update_vault_client_logger(self, log_level, logger):
            for vault_id, vault_config in self.__vault_configs.items():
                vault_config.get(OptionField.VAULT_CLIENT).set_logger(log_level, logger)

            for connection_id, connection_config in self.__connection_configs.items():
                connection_config.get(OptionField.VAULT_CLIENT).set_logger(log_level, logger)

        def _set_log_level(self, log_level):
            self._validate_log_level(self.__logger, log_level)
            self.__log_level = log_level
            self.__logger.set_log_level(log_level)
            if self._set_active_log_level is not None:
                self._set_active_log_level(log_level)
            self._update_vault_client_logger(log_level, self.__logger)
            log_info(self._skyflow_messages.Info.LOGGER_SETUP_DONE.value, self.__logger)
            log_info(self._skyflow_messages.Info.CURRENT_LOG_LEVEL.value.format(self.__log_level), self.__logger)

        def _add_skyflow_credentials(self, credentials):
            if credentials is not None:
                self.__skyflow_credentials = credentials
                self._validate_credentials(self.__logger, credentials)
                for vault_id, vault_config in self.__vault_configs.items():
                    vault_config.get(OptionField.VAULT_CLIENT).set_common_skyflow_credentials(credentials)

                for connection_id, connection_config in self.__connection_configs.items():
                    connection_config.get(OptionField.VAULT_CLIENT).set_common_skyflow_credentials(self.__skyflow_credentials)

        def build(self):
            self._validate_log_level(self.__logger, self.__log_level)
            self.__logger.set_log_level(self.__log_level)
            if self._set_active_log_level is not None:
                self._set_active_log_level(self.__log_level)

            for config in self.__vault_list:
                self._add_vault_config(config)

            for config in self.__connection_list:
                self._add_connection_config(config)

            self._update_vault_client_logger(self.__log_level, self.__logger)

            self._add_skyflow_credentials(self.__skyflow_credentials)

            return self._skyflow_cls(self)
