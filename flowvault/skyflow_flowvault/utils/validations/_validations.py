from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import ConfigField
from common.utils.enums import Env
from common.utils.validations import validate_keys, validate_required_field, validate_credentials, validate_log_level
from skyflow_flowvault.utils import SkyflowMessages
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.vault.data import InsertRecord, Upsert

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value

valid_vault_config_keys = [
    ConfigField.VAULT_ID,
    ConfigField.CLUSTER_ID,
    ConfigField.CREDENTIALS,
    ConfigField.ENV,
]


def validate_vault_config(logger, config):
    """v3's Builder-facade config validation, built from the same generic common-owned
    validators v2 uses."""
    validate_keys(logger, config, valid_vault_config_keys)

    validate_required_field(
        logger, config, ConfigField.VAULT_ID, str,
        CommonMessages.Error.EMPTY_VAULT_ID.value,
        CommonMessages.Error.INVALID_VAULT_ID.value
    )
    vault_id = config.get(ConfigField.VAULT_ID)

    validate_required_field(
        logger, config, ConfigField.CLUSTER_ID, str,
        CommonMessages.Error.EMPTY_CLUSTER_ID.value.format(vault_id),
        CommonMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id)
    )

    if ConfigField.CREDENTIALS in config and not config.get(ConfigField.CREDENTIALS):
        raise SkyflowError(CommonMessages.Error.EMPTY_CREDENTIALS.value.format("vault", vault_id), invalid_input_error_code)

    if ConfigField.CREDENTIALS in config and config.get(ConfigField.CREDENTIALS):
        validate_credentials(logger, config.get(ConfigField.CREDENTIALS), "vault", vault_id)

    if ConfigField.ENV in config and config.get(ConfigField.ENV) not in Env:
        raise SkyflowError(CommonMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    return True


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
    if not isinstance(request.records, list) or not all(isinstance(r, InsertRecord) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_INSERT.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    if len(request.records) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    if request.table is not None and (not isinstance(request.table, str) or not request.table.strip()):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_NAME_IN_INSERT.value, invalid_input_error_code)

    _validate_upsert(request.upsert)

    for record in request.records:
        if not isinstance(record.data, dict) or not record.data:
            raise SkyflowError(SkyflowMessages.Error.INVALID_RECORD_DATA_IN_INSERT.value, invalid_input_error_code)
        for key, value in record.data.items():
            if not isinstance(key, str) or not key.strip():
                raise SkyflowError(SkyflowMessages.Error.EMPTY_KEY_IN_INSERT_DATA.value, invalid_input_error_code)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise SkyflowError(SkyflowMessages.Error.EMPTY_VALUE_IN_INSERT_DATA.value, invalid_input_error_code)
        if record.table is not None and (not isinstance(record.table, str) or not record.table.strip()):
            raise SkyflowError(SkyflowMessages.Error.INVALID_TABLE_NAME_IN_INSERT.value, invalid_input_error_code)
        _validate_upsert(record.upsert)

    # table must be set in exactly one place -- request-level (every record) or per-record (no
    # partial mix) -- and upsert must live at that same place (mirrors Java's v3 Validations).
    table_at_request_level = request.table is not None

    if table_at_request_level:
        for record in request.records:
            if record.table is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_INSERT.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.table is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_INSERT.value, invalid_input_error_code)

    if table_at_request_level:
        for record in request.records:
            if record.upsert is not None:
                raise SkyflowError(SkyflowMessages.Error.RECORD_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
    else:
        if request.upsert is not None:
            raise SkyflowError(SkyflowMessages.Error.REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
