from abc import ABC, abstractmethod
from functools import partial

from common.utils.constants import OptionField
from common.utils.enums import LogLevel as _CommonLogLevel
from common.utils.logger import Logger as _CommonLogger
from common.utils.validations import (
    validate_vault_config as _common_validate_vault_config,
    validate_update_vault_config as _common_validate_update_vault_config,
    validate_log_level as _common_validate_log_level,
    validate_credentials as _common_validate_credentials,
)
from common.client.base_skyflow import BaseSkyflowImpl


class ConnectionCapable(ABC):
    @abstractmethod
    def add_connection_config(self, config):
        raise NotImplementedError

    @abstractmethod
    def remove_connection_config(self, connection_id):
        raise NotImplementedError

    @abstractmethod
    def update_connection_config(self, config):
        raise NotImplementedError

    @abstractmethod
    def get_connection_config(self, connection_id):
        raise NotImplementedError

    @abstractmethod
    def connection(self, connection_id=None):
        raise NotImplementedError


class DetectCapable(ABC):
    @abstractmethod
    def detect(self, vault_id=None):
        raise NotImplementedError


class ConnectionMixin(ConnectionCapable):

    def add_connection_config(self, config):
        builder = self._get_builder()
        builder._require_connections()
        builder._add_connection_config(config)
        return self

    def remove_connection_config(self, connection_id):
        builder = self._get_builder()
        builder._require_connections()
        builder.remove_connection_config(connection_id)
        return self

    def update_connection_config(self, config):
        builder = self._get_builder()
        builder._require_connections()
        builder.update_connection_config(config)
        return self

    def get_connection_config(self, connection_id):
        builder = self._get_builder()
        builder._require_connections()
        return builder.get_connection_config(connection_id).get(OptionField.VAULT_CLIENT).get_config()

    def connection(self, connection_id=None):
        builder = self._get_builder()
        builder._require_connections()
        connection_config = builder.get_connection_config(connection_id)
        return connection_config.get(OptionField.CONTROLLER)


class DetectMixin(DetectCapable):

    def detect(self, vault_id=None):
        builder = self._get_builder()
        builder._require_detect()
        vault_config = builder.get_vault_config(vault_id)
        return vault_config.get(OptionField.DETECT_CONTROLLER)


def make_skyflow_class(*, vault_client_cls, vault_controller_cls, skyflow_messages,
                        validate_vault_config=None, validate_update_vault_config=None,
                        validate_log_level=None, validate_credentials=None,
                        logger_cls=_CommonLogger, default_log_level=_CommonLogLevel.ERROR,
                        connection_cls=None, detect_cls=None,
                        validate_connection_config=None, validate_update_connection_config=None,
                        set_active_log_level=None, builder_mixins=()):

    if connection_cls is not None and (validate_connection_config is None or validate_update_connection_config is None):
        raise ValueError("connection_cls requires validate_connection_config and validate_update_connection_config")

    validate_vault_config = validate_vault_config or partial(_common_validate_vault_config, messages=skyflow_messages)
    validate_update_vault_config = validate_update_vault_config or partial(_common_validate_update_vault_config, messages=skyflow_messages)
    validate_log_level = validate_log_level or partial(_common_validate_log_level, messages=skyflow_messages)
    validate_credentials = validate_credentials or partial(_common_validate_credentials, messages=skyflow_messages)

    builder_attrs = {
        '_vault_client_cls': vault_client_cls,
        '_vault_controller_cls': vault_controller_cls,
        '_connection_cls': connection_cls,
        '_detect_cls': detect_cls,
        '_logger_cls': logger_cls,
        '_default_log_level': default_log_level,
        '_skyflow_messages': skyflow_messages,
        '_validate_vault_config': staticmethod(validate_vault_config),
        '_validate_update_vault_config': staticmethod(validate_update_vault_config),
        '_validate_connection_config': staticmethod(validate_connection_config) if validate_connection_config else None,
        '_validate_update_connection_config': staticmethod(validate_update_connection_config) if validate_update_connection_config else None,
        '_validate_log_level': staticmethod(validate_log_level),
        '_validate_credentials': staticmethod(validate_credentials),
        '_set_active_log_level': staticmethod(set_active_log_level) if set_active_log_level else None,
    }
    variant_builder = type('Builder', (*builder_mixins, BaseSkyflowImpl.Builder), builder_attrs)

    bases = [BaseSkyflowImpl]
    if connection_cls is not None:
        bases.append(ConnectionMixin)
    if detect_cls is not None:
        bases.append(DetectMixin)

    variant_skyflow = type('Skyflow', tuple(bases), {'Builder': variant_builder})
    variant_builder._skyflow_cls = variant_skyflow
    return variant_skyflow
