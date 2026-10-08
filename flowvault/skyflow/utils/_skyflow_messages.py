from enum import Enum

try:
    from ._version import SDK_VERSION
except ImportError:  # pragma: no cover
    SDK_VERSION = "0.0.0"

error_prefix = f"Skyflow Python SDK {SDK_VERSION}"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"


class SkyflowMessages:
    """v3's own operation-specific message catalog, mirroring v2's per-variant pattern. Generic
    infrastructure text lives in common.utils.SkyflowMessages instead."""

    class Error(Enum):
        INVALID_TIMEOUT = f"{error_prefix} Validation error. '{{}}' must be a positive number of seconds."
        INVALID_RETRY_SETTING = f"{error_prefix} Validation error. '{{}}' must be a non-negative integer."
        INVALID_VAULT_URL = f"{error_prefix} Validation error. 'vault_url' must be a non-empty string."
        EMPTY_RECORDS_IN_INSERT = f"{error_prefix} Insert failed. Specify at least one record to insert."
        INVALID_RECORDS_TYPE_IN_INSERT = f"{error_prefix} Insert failed. 'records' must be a list of InsertRequestRecord objects."
        INVALID_RECORD_DATA_IN_INSERT = f"{error_prefix} Validation error. Each record's 'values' must be a non-empty dict."
        INVALID_TABLE_NAME_IN_INSERT = f"{error_prefix} Validation error. 'table' must be a non-empty string."
        INVALID_UPSERT_TYPE_IN_INSERT = f"{error_prefix} Insert failed. 'upsert' must be an UpsertOptions object."
        INVALID_UPSERT_UNIQUE_COLUMNS_IN_INSERT = f"{error_prefix} Insert failed. Upsert's 'unique_columns' must be a non-empty list of strings."
        INVALID_UPSERT_UPDATE_TYPE_IN_INSERT = f"{error_prefix} Insert failed. Upsert's 'update_type' must be an UpsertType value."
        TABLE_NAME_IN_BOTH_PLACES_IN_INSERT = (
            f"{error_prefix} Insert failed. 'table' cannot be set on InsertRequest at the same "
            "time as any record's 'table' -- the vault accepts a table name outside the records "
            "(request-level, applying to all of them) or inside each record, but not both at once."
        )
        TABLE_NAME_MISSING_IN_INSERT = (
            f"{error_prefix} Insert failed. 'table' is not set on InsertRequest, so every record "
            "must set its own 'table' -- either set 'table' once at the request level, or set it "
            "individually on every record."
        )
        RECORD_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT = (
            f"{error_prefix} Insert failed. 'table' is set on InsertRequest (request-level), so "
            "'upsert' must also be provided at the request level -- a record cannot set its own "
            "'upsert' while 'table' is set at the request level."
        )
        REQUEST_LEVEL_UPSERT_NOT_ALLOWED_IN_INSERT = (
            f"{error_prefix} Insert failed. 'table' is set per-record, so 'upsert' must also be "
            "provided per-record -- InsertRequest's request-level 'upsert' cannot be used while "
            "'table' is set on individual records."
        )
        EMPTY_KEY_IN_INSERT_DATA = f"{error_prefix} Validation error. Each record's 'values' must not contain a null or empty key."
        EMPTY_VALUE_IN_INSERT_DATA = f"{error_prefix} Insert failed. Each record's 'values' must not contain a null or empty value."

        MISSING_TABLE_NAME_IN_GET = f"{error_prefix} Get failed. Specify a table name."
        MISSING_IDS_OR_UNIQUE_VALUES_IN_GET = f"{error_prefix} Get failed. Specify at least one of 'ids' or 'unique_values'."
        INVALID_IDS_IN_GET = f"{error_prefix} Get failed. 'ids' must be a non-empty list of strings."
        INVALID_RECORDS_TYPE_IN_GET = f"{error_prefix} Get failed. 'records' must be a non-empty list of GetRequestRecord objects."
        GET_MODE_CONFLICT = f"{error_prefix} Get failed. Use either 'records' (multi-table) or the single-table fields (table/ids/unique_values/columns/column_redactions/limit/offset), not both."

        EMPTY_RECORDS_IN_UPDATE = f"{error_prefix} Update failed. Specify at least one record to update."
        INVALID_RECORDS_TYPE_IN_UPDATE = f"{error_prefix} Update failed. 'records' must be a list of UpdateRequestRecord objects."
        MISSING_SKYFLOW_ID_IN_UPDATE = f"{error_prefix} Update failed. Each record must specify a non-empty 'skyflow_id'."
        MISSING_DATA_IN_UPDATE = f"{error_prefix} Update failed. Each record must specify a non-empty 'data' object."
        INVALID_DATA_TYPE_IN_UPDATE = f"{error_prefix} Update failed. Each record's 'data' must be a dict."
        INVALID_UPDATE_TYPE_IN_UPDATE = f"{error_prefix} Update failed. 'update_type' must be an UpsertType value."
        TABLE_NAME_IN_BOTH_PLACES_IN_UPDATE = (
            f"{error_prefix} Update failed. 'table' cannot be set on UpdateRequest at the same "
            "time as any record's 'table' -- specify a table name outside the records "
            "(request-level, applying to all of them) or inside each record, but not both at once."
        )
        TABLE_NAME_MISSING_IN_UPDATE = (
            f"{error_prefix} Update failed. 'table' is not set on UpdateRequest, so every record "
            "must set its own 'table' -- either set 'table' once at the request level, or set it "
            "individually on every record."
        )

        MISSING_TABLE_NAME_IN_DELETE = f"{error_prefix} Delete failed. Specify a table name."
        MISSING_IDS_OR_UNIQUE_VALUES_IN_DELETE = f"{error_prefix} Delete failed. Specify at least one of 'ids' or 'unique_values'."
        INVALID_IDS_IN_DELETE = f"{error_prefix} Delete failed. 'ids' must be a non-empty list of strings."

        EMPTY_TOKENS_IN_DETOKENIZE = f"{error_prefix} Detokenize failed. Specify at least one token to detokenize."
        INVALID_TOKENS_TYPE_IN_DETOKENIZE = f"{error_prefix} Detokenize failed. 'tokens' must be a non-empty list of strings."
        INVALID_TOKEN_GROUP_REDACTIONS_IN_DETOKENIZE = f"{error_prefix} Detokenize failed. 'token_group_redactions' must be a list of TokenGroupRedactions objects with a non-empty 'token_group_name'."

        INVALID_QUERY_IN_QUERY = f"{error_prefix} Query failed. 'query' must be a non-empty string."

        INVALID_RECORDS_TYPE_IN_GET_TOKENS = f"{error_prefix} Get tokens failed. 'records' must be a non-empty list of GetTokensRequestRecord objects."
        MISSING_VALUE_IN_GET_TOKENS = f"{error_prefix} Get tokens failed. Each record must specify a non-null 'value'."
        MISSING_TOKEN_GROUP_NAME_IN_GET_TOKENS = f"{error_prefix} Get tokens failed. Each record must specify a non-empty 'token_group_name'."

        INVALID_RECORDS_TYPE_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. 'records' must be a non-empty list of UploadFilesRequestRecord objects."
        MISSING_TABLE_NAME_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Each record must specify a non-empty 'table_name'."
        INVALID_COLUMNS_TYPE_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Each record's 'columns' must be a non-empty list of UploadFilesRequestColumn objects."
        MISSING_COLUMN_NAME_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Each column must specify a non-empty 'column'."
        MISSING_FILE_SOURCE_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Each column must specify exactly one of 'file_path', 'base64' or 'file_object'."
        MULTIPLE_FILE_SOURCES_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Provide only one of 'file_path', 'base64' or 'file_object' per column."
        MISSING_FILE_NAME_FOR_BASE64_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. 'file_name' is required when 'base64' is used."
        FILE_NOT_FOUND_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Could not read file at path '{{}}'."
        INVALID_BASE64_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. 'base64' content for column '{{}}' could not be decoded."
        DUPLICATE_COLUMN_IN_UPLOAD_FILES = f"{error_prefix} Upload files failed. Column '{{}}' is specified more than once in a record. Each column may appear only once per record."

        INVALID_RECORDS_TYPE_IN_DELETE_FILES = f"{error_prefix} Delete files failed. 'records' must be a non-empty list of DeleteFilesRequestRecord objects."
        MISSING_TABLE_NAME_IN_DELETE_FILES = f"{error_prefix} Delete files failed. Each record must specify a non-empty 'table_name'."
        INVALID_COLUMNS_IN_DELETE_FILES = f"{error_prefix} Delete files failed. Each record's 'columns' must be a non-empty list of strings."
        INVALID_ID_OR_UNIQUE_VALUES_IN_DELETE_FILES = f"{error_prefix} Delete files failed. Set exactly one of 'skyflow_id' or 'unique_values' per record."
        DUPLICATE_COLUMN_IN_DELETE_FILES = f"{error_prefix} Delete files failed. Column '{{}}' is specified more than once in a record. Each column may appear only once per record."

    class Info(Enum):
        VALIDATE_INSERT_REQUEST = f"{INFO}: [{error_prefix}] Validating insert request."
        INSERT_TRIGGERED = f"{INFO}: [{error_prefix}] Insert method triggered."
        INSERT_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Insert request resolved."
        INSERT_SUCCESS = f"{INFO}: [{error_prefix}] Data inserted."

        VALIDATE_GET_REQUEST = f"{INFO}: [{error_prefix}] Validating get request."
        GET_TRIGGERED = f"{INFO}: [{error_prefix}] Get method triggered."
        GET_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Get request resolved."
        GET_SUCCESS = f"{INFO}: [{error_prefix}] Data fetched."

        VALIDATE_UPDATE_REQUEST = f"{INFO}: [{error_prefix}] Validating update request."
        UPDATE_TRIGGERED = f"{INFO}: [{error_prefix}] Update method triggered."
        UPDATE_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Update request resolved."
        UPDATE_SUCCESS = f"{INFO}: [{error_prefix}] Data updated."

        VALIDATE_DELETE_REQUEST = f"{INFO}: [{error_prefix}] Validating delete request."
        DELETE_TRIGGERED = f"{INFO}: [{error_prefix}] Delete method triggered."
        DELETE_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Delete request resolved."
        DELETE_SUCCESS = f"{INFO}: [{error_prefix}] Data deleted."

        VALIDATE_DETOKENIZE_REQUEST = f"{INFO}: [{error_prefix}] Validating detokenize request."
        DETOKENIZE_TRIGGERED = f"{INFO}: [{error_prefix}] Detokenize method triggered."
        DETOKENIZE_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Detokenize request resolved."
        DETOKENIZE_SUCCESS = f"{INFO}: [{error_prefix}] Tokens detokenized."

        VALIDATE_QUERY_REQUEST = f"{INFO}: [{error_prefix}] Validating query request."
        QUERY_TRIGGERED = f"{INFO}: [{error_prefix}] Query method triggered."
        QUERY_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Query request resolved."
        QUERY_SUCCESS = f"{INFO}: [{error_prefix}] Query executed."

        VALIDATE_GET_TOKENS_REQUEST = f"{INFO}: [{error_prefix}] Validating get tokens request."
        GET_TOKENS_TRIGGERED = f"{INFO}: [{error_prefix}] Get tokens method triggered."
        GET_TOKENS_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Get tokens request resolved."
        GET_TOKENS_SUCCESS = f"{INFO}: [{error_prefix}] Tokens fetched."

        VALIDATE_UPLOAD_FILES_REQUEST = f"{INFO}: [{error_prefix}] Validating upload files request."
        UPLOAD_FILES_TRIGGERED = f"{INFO}: [{error_prefix}] Upload files method triggered."
        UPLOAD_FILES_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Upload files request resolved."
        UPLOAD_FILES_SUCCESS = f"{INFO}: [{error_prefix}] Files uploaded."

        VALIDATE_DELETE_FILES_REQUEST = f"{INFO}: [{error_prefix}] Validating delete files request."
        DELETE_FILES_TRIGGERED = f"{INFO}: [{error_prefix}] Delete files method triggered."
        DELETE_FILES_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Delete files request resolved."
        DELETE_FILES_SUCCESS = f"{INFO}: [{error_prefix}] Files deleted."

    class ErrorLogs(Enum):
        INSERT_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Insert call resulted in failure."
        GET_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Get call resulted in failure."
        UPDATE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Update call resulted in failure."
        DELETE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Delete call resulted in failure."
        DETOKENIZE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Detokenize call resulted in failure."
        QUERY_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Query call resulted in failure."
        GET_TOKENS_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Get tokens call resulted in failure."
        UPLOAD_FILES_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Upload files call resulted in failure."
        DELETE_FILES_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Delete files call resulted in failure."
