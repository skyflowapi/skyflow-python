from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.validations import (
    validate_keys,
    validate_credentials,
    validate_vault_config,
    validate_update_vault_config,
)
from skyflow_flowvault.utils import SkyflowMessages
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import Upsert

VALID_INSERT_RECORD_KEYS = ["values", "table", "upsert"]

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value

# validate_vault_config/validate_update_vault_config/validate_credentials are re-exported
# directly from common.utils.validations -- flowvault's own logic here was field-for-field
# identical to v2's, confirmed, so both variants now share one implementation.


def _validate_upsert(upsert):
    if upsert is None:
        return
    if not isinstance(upsert, Upsert):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_TYPE_IN_INSERT.value, invalid_input_error_code)
    if (not isinstance(upsert.unique_columns, list) or not upsert.unique_columns
            or not all(isinstance(c, str) for c in upsert.unique_columns)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UNIQUE_COLUMNS_IN_INSERT.value, invalid_input_error_code)
    if upsert.update_type is not None and not isinstance(upsert.update_type, UpsertType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UPDATE_TYPE_IN_INSERT.value, invalid_input_error_code)


MAX_INSERT_RECORDS = 10000  # matches Java's v3 Validations.validateInsertRequest (hardcoded, not configurable)


def validate_insert_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, dict) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_INSERT.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    if len(request.records) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    # request.table/record["table"] format and record["values"] emptiness/key/value validity are
    # checked by the controller via the shared BaseVaultController._validate_table_name_if_present()
    # / _validate_field_values() -- not here, to avoid duplicating that logic.

    _validate_upsert(request.upsert)

    for record in request.records:
        validate_keys(logger, record, VALID_INSERT_RECORD_KEYS)
        _validate_upsert(record.get("upsert"))

    # table must be set in exactly one place -- request-level (every record) or per-record (no
    # partial mix) -- and upsert must live at that same place (mirrors Java's v3 Validations).
    table_at_request_level = request.table is not None

    if table_at_request_level:
        for record in request.records:
            if record.get("table") is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_INSERT.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.get("table") is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_INSERT.value, invalid_input_error_code)

    if table_at_request_level:
        for record in request.records:
            if record.get("upsert") is not None:
                raise SkyflowError(SkyflowMessages.Error.RECORD_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
    else:
        if request.upsert is not None:
            raise SkyflowError(SkyflowMessages.Error.REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
