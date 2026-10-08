from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.validations import (
    validate_keys,
    validate_credentials,
    validate_non_empty_string_list,
)
from common.utils.validations import validate_vault_config as _common_validate_vault_config
from common.utils.validations import validate_update_vault_config as _common_validate_update_vault_config
from skyflow.utils import SkyflowMessages
from skyflow.utils.enums import UpsertType
from skyflow.utils._http_config import (
    POSITIVE_SECOND_KEYS,
    NON_NEGATIVE_INT_KEYS,
    VAULT_URL_KEY,
    VAULT_CONFIG_KEYS,
)
from skyflow.vault.data import (
    GetRequestRecord,
    InsertRequestRecord,
    UpdateRequestRecord,
    UpsertOptions,
    TokenGroupRedactions,
    GetTokensRequestRecord,
    UploadFilesRequestRecord,
    UploadFilesRequestColumn,
    DeleteFilesRequestRecord,
)

VALID_UPDATE_RECORD_KEYS = ["skyflow_id", "data", "tokens", "table_name"]

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_http_config_value(key, value):
    if key in POSITIVE_SECOND_KEYS:
        if not _is_number(value) or value <= 0:
            raise SkyflowError(SkyflowMessages.Error.INVALID_TIMEOUT.value.format(key), invalid_input_error_code)
    elif key in NON_NEGATIVE_INT_KEYS:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SkyflowError(SkyflowMessages.Error.INVALID_RETRY_SETTING.value.format(key), invalid_input_error_code)


def _validate_http_config(logger, config):
    for key in (*POSITIVE_SECOND_KEYS, *NON_NEGATIVE_INT_KEYS):
        if key in config:
            validate_http_config_value(key, config[key])
    if VAULT_URL_KEY in config:
        vault_url = config[VAULT_URL_KEY]
        if not isinstance(vault_url, str) or not vault_url:
            raise SkyflowError(SkyflowMessages.Error.INVALID_VAULT_URL.value, invalid_input_error_code)


def validate_vault_config(logger, config):
    _validate_http_config(logger, config)
    return _common_validate_vault_config(logger, config, messages=CommonMessages, allowed_keys=VAULT_CONFIG_KEYS)


def validate_update_vault_config(logger, config):
    _validate_http_config(logger, config)
    return _common_validate_update_vault_config(logger, config, messages=CommonMessages, allowed_keys=VAULT_CONFIG_KEYS)


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


def validate_insert_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, InsertRequestRecord) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_INSERT.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_INSERT.value, invalid_input_error_code)

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
            request.table_name or request.skyflow_ids or request.unique_values or request.columns
            or request.column_redactions or request.limit is not None or request.offset is not None
        )
        if single_table_fields_set:
            raise SkyflowError(SkyflowMessages.Error.GET_MODE_CONFLICT.value, invalid_input_error_code)
        if (not isinstance(request.records, list) or not request.records
                or not all(isinstance(r, GetRequestRecord) for r in request.records)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_GET.value, invalid_input_error_code)
        for record in request.records:
            if not record.table_name:
                raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_GET.value, invalid_input_error_code)
            if not record.skyflow_ids and not record.unique_values:
                raise SkyflowError(SkyflowMessages.Error.MISSING_IDS_OR_UNIQUE_VALUES_IN_GET.value, invalid_input_error_code)
            if record.skyflow_ids is not None:
                validate_non_empty_string_list(logger, record.skyflow_ids, SkyflowMessages.Error.INVALID_IDS_IN_GET.value)
        return

    if not request.table_name:
        raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_GET.value, invalid_input_error_code)

    if not request.skyflow_ids and not request.unique_values:
        raise SkyflowError(SkyflowMessages.Error.MISSING_IDS_OR_UNIQUE_VALUES_IN_GET.value, invalid_input_error_code)

    if request.skyflow_ids is not None:
        validate_non_empty_string_list(logger, request.skyflow_ids, SkyflowMessages.Error.INVALID_IDS_IN_GET.value)


def validate_update_request(logger, request):
    if not isinstance(request.records, list) or not all(isinstance(r, UpdateRequestRecord) for r in request.records):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_UPDATE.value, invalid_input_error_code)

    if not request.records:
        raise SkyflowError(SkyflowMessages.Error.EMPTY_RECORDS_IN_UPDATE.value, invalid_input_error_code)

    if request.update_type is not None and not isinstance(request.update_type, UpsertType):
        raise SkyflowError(SkyflowMessages.Error.INVALID_UPDATE_TYPE_IN_UPDATE.value, invalid_input_error_code)

    for record in request.records:
        skyflow_id = record.skyflow_id
        if not isinstance(skyflow_id, str) or not skyflow_id.strip():
            raise SkyflowError(SkyflowMessages.Error.MISSING_SKYFLOW_ID_IN_UPDATE.value, invalid_input_error_code)
        data = record.data
        if data is None:
            raise SkyflowError(SkyflowMessages.Error.MISSING_DATA_IN_UPDATE.value, invalid_input_error_code)
        if not isinstance(data, dict):
            raise SkyflowError(SkyflowMessages.Error.INVALID_DATA_TYPE_IN_UPDATE.value, invalid_input_error_code)
        if not data:
            raise SkyflowError(SkyflowMessages.Error.MISSING_DATA_IN_UPDATE.value, invalid_input_error_code)

    table_at_request_level = request.table_name is not None

    if table_at_request_level:
        for record in request.records:
            if record.table_name is not None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_IN_BOTH_PLACES_IN_UPDATE.value, invalid_input_error_code)
    else:
        for record in request.records:
            if record.table_name is None:
                raise SkyflowError(SkyflowMessages.Error.TABLE_NAME_MISSING_IN_UPDATE.value, invalid_input_error_code)


def validate_delete_request(logger, request):
    if not request.table_name:
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
                isinstance(entry, TokenGroupRedactions)
                and isinstance(entry.token_group_name, str) and entry.token_group_name.strip()
                for entry in request.token_group_redactions
            )
        )
        if not valid:
            raise SkyflowError(SkyflowMessages.Error.INVALID_TOKEN_GROUP_REDACTIONS_IN_DETOKENIZE.value, invalid_input_error_code)


def validate_query_request(logger, request):
    if not isinstance(request.query, str) or not request.query.strip():
        raise SkyflowError(SkyflowMessages.Error.INVALID_QUERY_IN_QUERY.value, invalid_input_error_code)


def validate_get_tokens_request(logger, request):
    if (not isinstance(request.records, list) or not request.records
            or not all(isinstance(r, GetTokensRequestRecord) for r in request.records)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_GET_TOKENS.value, invalid_input_error_code)

    for record in request.records:
        if record.value is None:
            raise SkyflowError(SkyflowMessages.Error.MISSING_VALUE_IN_GET_TOKENS.value, invalid_input_error_code)
        if not isinstance(record.token_group_name, str) or not record.token_group_name.strip():
            raise SkyflowError(SkyflowMessages.Error.MISSING_TOKEN_GROUP_NAME_IN_GET_TOKENS.value, invalid_input_error_code)


def validate_upload_files_request(logger, request):
    if (not isinstance(request.records, list) or not request.records
            or not all(isinstance(r, UploadFilesRequestRecord) for r in request.records)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_UPLOAD_FILES.value, invalid_input_error_code)

    for record in request.records:
        if not isinstance(record.table_name, str) or not record.table_name.strip():
            raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_UPLOAD_FILES.value, invalid_input_error_code)
        if (not isinstance(record.columns, list) or not record.columns
                or not all(isinstance(c, UploadFilesRequestColumn) for c in record.columns)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMNS_TYPE_IN_UPLOAD_FILES.value, invalid_input_error_code)
        seen_columns = set()
        for column in record.columns:
            if not isinstance(column.column, str) or not column.column.strip():
                raise SkyflowError(SkyflowMessages.Error.MISSING_COLUMN_NAME_IN_UPLOAD_FILES.value, invalid_input_error_code)
            if column.column in seen_columns:
                raise SkyflowError(SkyflowMessages.Error.DUPLICATE_COLUMN_IN_UPLOAD_FILES.value.format(column.column), invalid_input_error_code)
            seen_columns.add(column.column)
            sources = [column.file_path, column.base64, column.file_object]
            provided = [source for source in sources if source is not None]
            if not provided:
                raise SkyflowError(SkyflowMessages.Error.MISSING_FILE_SOURCE_IN_UPLOAD_FILES.value, invalid_input_error_code)
            if len(provided) > 1:
                raise SkyflowError(SkyflowMessages.Error.MULTIPLE_FILE_SOURCES_IN_UPLOAD_FILES.value, invalid_input_error_code)
            if column.base64 is not None and (not isinstance(column.file_name, str) or not column.file_name.strip()):
                raise SkyflowError(SkyflowMessages.Error.MISSING_FILE_NAME_FOR_BASE64_IN_UPLOAD_FILES.value, invalid_input_error_code)


def validate_delete_files_request(logger, request):
    if (not isinstance(request.records, list) or not request.records
            or not all(isinstance(r, DeleteFilesRequestRecord) for r in request.records)):
        raise SkyflowError(SkyflowMessages.Error.INVALID_RECORDS_TYPE_IN_DELETE_FILES.value, invalid_input_error_code)

    for record in request.records:
        if not isinstance(record.table_name, str) or not record.table_name.strip():
            raise SkyflowError(SkyflowMessages.Error.MISSING_TABLE_NAME_IN_DELETE_FILES.value, invalid_input_error_code)
        if (not isinstance(record.columns, list) or not record.columns
                or not all(isinstance(c, str) and c.strip() for c in record.columns)):
            raise SkyflowError(SkyflowMessages.Error.INVALID_COLUMNS_IN_DELETE_FILES.value, invalid_input_error_code)
        seen_columns = set()
        for column in record.columns:
            if column in seen_columns:
                raise SkyflowError(SkyflowMessages.Error.DUPLICATE_COLUMN_IN_DELETE_FILES.value.format(column), invalid_input_error_code)
            seen_columns.add(column)
        has_skyflow_id = isinstance(record.skyflow_id, str) and bool(record.skyflow_id.strip())
        has_unique_values = isinstance(record.unique_values, list) and bool(record.unique_values)
        if has_skyflow_id == has_unique_values:
            raise SkyflowError(SkyflowMessages.Error.INVALID_ID_OR_UNIQUE_VALUES_IN_DELETE_FILES.value, invalid_input_error_code)
