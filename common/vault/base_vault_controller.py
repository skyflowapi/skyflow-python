from abc import ABC, abstractmethod

from common.errors import SkyflowError
from common.utils import SkyflowMessages as _CommonSkyflowMessages
from common.vault.data import BaseInsertRequest, BaseInsertResponse

_INVALID_INPUT_ERROR_CODE = _CommonSkyflowMessages.ErrorCodes.INVALID_INPUT.value


class IVaultController(ABC):

    @abstractmethod
    def insert(self, request: BaseInsertRequest) -> BaseInsertResponse:
        raise NotImplementedError

    @abstractmethod
    def get(self, request):
        raise NotImplementedError

    @abstractmethod
    def update(self, request):
        raise NotImplementedError

    @abstractmethod
    def delete(self, request):
        raise NotImplementedError

    @abstractmethod
    def query(self, request):
        raise NotImplementedError

    @abstractmethod
    def detokenize(self, request):
        raise NotImplementedError


class BaseVaultController(IVaultController):

    _skyflow_messages = None

    def __init__(self, vault_client):
        self._vault_client = vault_client

    def _validate_table_name_if_present(self, table):
        if table is not None and (not isinstance(table, str) or not table.strip()):
            raise SkyflowError(
                self._skyflow_messages.Error.INVALID_TABLE_NAME_IN_INSERT.value,
                _INVALID_INPUT_ERROR_CODE,
            )

    def _validate_field_values(self, values):
        if not isinstance(values, dict) or not values:
            raise SkyflowError(
                self._skyflow_messages.Error.INVALID_RECORD_DATA_IN_INSERT.value,
                _INVALID_INPUT_ERROR_CODE,
            )
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise SkyflowError(
                    self._skyflow_messages.Error.EMPTY_KEY_IN_INSERT_DATA.value,
                    _INVALID_INPUT_ERROR_CODE,
                )
