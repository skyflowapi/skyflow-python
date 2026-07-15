from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.validations import (
    validate_keys,
    validate_credentials,
    validate_non_empty_string_list,
    validate_vault_config,
    validate_update_vault_config,
)
from skyflow_flowvault.utils import SkyflowMessages
from skyflow_flowvault.utils.enums import UpsertType

VALID_INSERT_RECORD_KEYS = ["values", "table", "upsert"]
VALID_UPSERT_KEYS = ["update_type", "unique_columns"]
VALID_UPDATE_RECORD_KEYS = ["skyflow_id", "values", "tokens", "table"]

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value

# validate_vault_config/validate_update_vault_config/validate_credentials are re-exported
# directly from common.utils.validations -- flowvault's own logic here was field-for-field
# identical to v2's, confirmed, so both variants now share one implementation.


def _validate_upsert(logger, upsert):
    if upsert is None:
        return
    if not isinstance(upsert, dict):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_TYPE_IN_INSERT.value, invalid_input_error_code)
    validate_keys(logger, upsert, VALID_UPSERT_KEYS)
    unique_columns = upsert.get("unique_columns")
    if (not isinstance(unique_columns, list) or not unique_columns
            or not all(isinstance(c, str) for c in unique_columns)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UNIQUE_COLUMNS_IN_INSERT.value, invalid_input_error_code)
    update_type = upsert.get("update_type")
    if update_type is not None and not isinstance(update_type, UpsertType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UPDATE_TYPE_IN_INSERT.value, invalid_input_error_code)


MAX_INSERT_RECORDS = 10000  # matches Java's v3 Validations.validateInsertRequest (hardcoded, not configurable)


def validate_insert_request(logger, request):
    if not isinstance(request.values, list) or not all(isinstance(r, dict) for r in request.values):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_INSERT.value, invalid_input_error_code)

    if not request.values:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    if len(request.values) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    # request.table/record["table"] format and record["values"] emptiness/key/value validity are
    # checked by the controller via the shared BaseVaultController._validate_table_name_if_present()
    # / _validate_field_values() -- not here, to avoid duplicating that logic.

    _validate_upsert(logger, request.upsert)

    for record in request.values:
        validate_keys(logger, record, VALID_INSERT_RECORD_KEYS)
        _validate_upsert(logger, record.get("upsert"))

    # table must be set in exactly one place -- request-level (every record) or per-record (no
    # partial mix) -- and upsert must live at that same place (mirrors Java's v3 Validations).
    table_at_request_level = request.table is not None

    if table_at_request_level:
        for record in request.values:
            if record.get("table") is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_INSERT.value, invalid_input_error_code)
    else:
        for record in request.values:
            if record.get("table") is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_INSERT.value, invalid_input_error_code)

    if table_at_request_level:
        for record in request.values:
            if record.get("upsert") is not None:
                raise SkyflowError(SkyflowMessages.Error.RECORD_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
    else:
        if request.upsert is not None:
            raise SkyflowError(SkyflowMessages.Error.REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)


def validate_get_request(logger, request):
    if not request.table:
        raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_GET.value, invalid_input_error_code)

    if not request.ids and not request.unique_values:
        raise SkyflowError(SkyflowMessages.Error.MISSING_IDS_OR_UNIQUE_VALUES_IN_GET.value, invalid_input_error_code)

    if request.ids is not None:
        validate_non_empty_string_list(logger, request.ids, SkyflowMessages.Error.INVALID_IDS_IN_GET.value)


def validate_update_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, dict) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_UPDATE.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_UPDATE.value, invalid_input_error_code)

    if request.update_type is not None and not isinstance(request.update_type, UpsertType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPDATE_TYPE_IN_UPDATE.value, invalid_input_error_code)

    for record in request.records:
        validate_keys(logger, record, VALID_UPDATE_RECORD_KEYS)
        skyflow_id = record.get("skyflow_id")
        if not isinstance(skyflow_id, str) or not skyflow_id.strip():
            raise SkyflowError(SkyflowMessages.Error.MISSING_SKYFLOW_ID_IN_UPDATE.value, invalid_input_error_code)

    table_at_request_level = request.table is not None

    if table_at_request_level:
        for record in request.records:
            if record.get("table") is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_UPDATE.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.get("table") is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_UPDATE.value, invalid_input_error_code)


def validate_delete_request(logger, request):
    if not request.table:
        raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_DELETE.value, invalid_input_error_code)

    if not request.ids and not request.unique_values:
        raise SkyflowError(SkyflowMessages.Error.MISSING_IDS_OR_UNIQUE_VALUES_IN_DELETE.value, invalid_input_error_code)

    if request.ids is not None:
        validate_non_empty_string_list(logger, request.ids, SkyflowMessages.Error.INVALID_IDS_IN_DELETE.value)


def validate_detokenize_request(logger, request):
    if (
        not isinstance(request.tokens, list) or not all(isinstance(t, str) and t.strip() for t in request.tokens)
    ):
        raise SkyflowError(SkyflowMessages.Error.INVALID_TOKENS_TYPE_IN_DETOKENIZE.value, invalid_input_error_code)

    if not request.tokens:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_TOKENS_IN_DETOKENIZE.value, invalid_input_error_code)

    if request.token_group_redactions is not None:
        valid = (
            isinstance(request.token_group_redactions, list)
            and all(
                isinstance(entry, dict) and isinstance(entry.get("token_group_name"), str) and entry.get("token_group_name").strip()
                for entry in request.token_group_redactions
            )
        )
        if not valid:
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_GROUP_REDACTIONS_IN_DETOKENIZE.value, invalid_input_error_code)


def validate_tokenize_request(logger, request):
    if not isinstance(request.values, list) or not all(isinstance(v, dict) for v in request.values):
        raise SkyflowError(SkyflowMessages.Error.INVALID_VALUES_TYPE_IN_TOKENIZE.value, invalid_input_error_code)

    if not request.values:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_VALUES_IN_TOKENIZE.value, invalid_input_error_code)

    for value in request.values:
        token_group_names = value.get("token_group_names")
        validate_non_empty_string_list(
            logger, token_group_names, SkyflowMessages.Error.MISSING_TOKEN_GROUP_NAMES_IN_TOKENIZE.value
        )
