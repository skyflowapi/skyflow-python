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
from skyflow_flowvault.vault.data import GetRecordRequest, BulkInsertRecord, InsertRequestRecord, UpsertOptions

VALID_UPDATE_RECORD_KEYS = ["skyflow_id", "data", "tokens", "table_name"]

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value


def _validate_upsert(logger, upsert):
    if upsert is None:
        return
    if not isinstance(upsert, UpsertOptions):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_TYPE_IN_INSERT.value, invalid_input_error_code)
    unique_columns = upsert.unique_columns
    if (not isinstance(unique_columns, list) or not unique_columns
            or not all(isinstance(c, str) for c in unique_columns)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UNIQUE_COLUMNS_IN_INSERT.value, invalid_input_error_code)
    if upsert.update_type is not None and not isinstance(upsert.update_type, UpsertType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPSERT_UPDATE_TYPE_IN_INSERT.value, invalid_input_error_code)


MAX_INSERT_RECORDS = 10000


def validate_insert_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, InsertRequestRecord) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_INSERT.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    if len(request.records) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_RECORDS_IN_INSERT.value, invalid_input_error_code)

    _validate_upsert(logger, request.upsert)
    for record in request.records:
        _validate_upsert(logger, record.upsert)

    table_at_request_level = request.table_name is not None

    if table_at_request_level:
        for record in request.records:
            if record.table_name is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_INSERT.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.table_name is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_INSERT.value, invalid_input_error_code)

    if table_at_request_level:
        for record in request.records:
            if record.upsert is not None:
                raise SkyflowError(SkyflowMessages.Error.RECORD_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)
    elif request.upsert is not None:
        raise SkyflowError(SkyflowMessages.Error.REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)


def validate_get_request(logger, request):
    if request.records is not None:
        single_table_fields_set = (
            request.table or request.ids or request.unique_values or request.columns
            or request.column_redactions or request.limit is not None or request.offset is not None
        )
        if single_table_fields_set:
            raise SkyflowError(SkyflowMessages.Error.GET_MODE_CONFLICT.value, invalid_input_error_code)
        if (not isinstance(request.records, list) or not request.records
                or not all(isinstance(r, GetRecordRequest) for r in request.records)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_GET.value, invalid_input_error_code)
        for record in request.records:
            if not record.table:
                raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_GET.value, invalid_input_error_code)
            if not record.ids and not record.unique_values:
                raise SkyflowError(SkyflowMessages.Error.MISSING_IDS_OR_UNIQUE_VALUES_IN_GET.value, invalid_input_error_code)
            if record.ids is not None:
                validate_non_empty_string_list(logger, record.ids, SkyflowMessages.Error.INVALID_IDS_IN_GET.value)
        return

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

    table_at_request_level = request.table_name is not None

    if table_at_request_level:
        for record in request.records:
            if record.get("table_name") is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_UPDATE.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.get("table_name") is None:
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


def validate_query_request(logger, request):
    if not isinstance(request.query, str) or not request.query.strip():
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_IN_QUERY.value, invalid_input_error_code)


def validate_bulk_insert_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, BulkInsertRecord) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_BULK_INSERT.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_BULK_INSERT.value, invalid_input_error_code)

    if len(request.records) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_RECORDS_IN_BULK_INSERT.value, invalid_input_error_code)

    _validate_upsert(logger, request.upsert)
    for record in request.records:
        _validate_upsert(logger, record.upsert)

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
    elif request.upsert is not None:
        raise SkyflowError(SkyflowMessages.Error.REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT.value, invalid_input_error_code)


def validate_bulk_detokenize_request(logger, request):
    validate_detokenize_request(logger, request)
    if len(request.tokens) > MAX_INSERT_RECORDS:
        raise SkyflowError(SkyflowMessages.Error.TOO_MANY_TOKENS_IN_BULK_DETOKENIZE.value, invalid_input_error_code)
