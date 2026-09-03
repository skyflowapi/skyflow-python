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
        TOO_MANY_RECORDS_IN_INSERT = f"{error_prefix} Insert failed. A single insert request cannot contain more than 10000 records."
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
        INVALID_RECORDS_TYPE_IN_GET = f"{error_prefix} Get failed. 'records' must be a non-empty list of GetRecordRequest objects."
        GET_MODE_CONFLICT = f"{error_prefix} Get failed. Use either 'records' (multi-table) or the single-table fields (table/ids/unique_values/columns/column_redactions/limit/offset), not both."

        EMPTY_RECORDS_IN_UPDATE = f"{error_prefix} Update failed. Specify at least one record to update."
        INVALID_RECORDS_TYPE_IN_UPDATE = f"{error_prefix} Update failed. 'records' must be a list of dicts."
        MISSING_SKYFLOW_ID_IN_UPDATE = f"{error_prefix} Update failed. Each record must specify a non-empty 'skyflow_id'."
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


        EMPTY_RECORDS_IN_BULK_INSERT = f"{error_prefix} Bulk insert failed. Specify at least one record to insert."
        INVALID_RECORDS_TYPE_IN_BULK_INSERT = f"{error_prefix} Bulk insert failed. 'records' must be a list of BulkInsertRequestRecord objects."
        INVALID_RECORD_IN_BULK_INSERT = f"{error_prefix} Bulk insert failed. Each record must be a BulkInsertRequestRecord object."
        TOO_MANY_RECORDS_IN_BULK_INSERT = f"{error_prefix} Bulk insert failed. A single bulk insert request cannot contain more than 10000 records."
        TOO_MANY_TOKENS_IN_BULK_DETOKENIZE = f"{error_prefix} Bulk detokenize failed. A single bulk detokenize request cannot contain more than 10000 tokens."

        INVALID_BATCH_SIZE = f"{error_prefix} Invalid batch size provided. Falling back to the default batch size."
        BATCH_SIZE_EXCEEDS_MAX = f"{error_prefix} Batch size exceeds the maximum allowed. Using the maximum batch size."
        INVALID_CONCURRENCY_LIMIT = f"{error_prefix} Invalid concurrency limit provided. Falling back to the default concurrency limit."
        CONCURRENCY_EXCEEDS_MAX = f"{error_prefix} Concurrency limit exceeds the maximum allowed. Using the maximum concurrency limit."

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


        VALIDATE_BULK_INSERT_REQUEST = f"{INFO}: [{error_prefix}] Validating bulk insert request."
        BULK_INSERT_TRIGGERED = f"{INFO}: [{error_prefix}] Bulk insert method triggered."
        BULK_INSERT_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Bulk insert request resolved."
        BULK_INSERT_SUCCESS = f"{INFO}: [{error_prefix}] Bulk insert completed."

        VALIDATE_BULK_DETOKENIZE_REQUEST = f"{INFO}: [{error_prefix}] Validating bulk detokenize request."
        BULK_DETOKENIZE_TRIGGERED = f"{INFO}: [{error_prefix}] Bulk detokenize method triggered."
        BULK_DETOKENIZE_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Bulk detokenize request resolved."
        BULK_DETOKENIZE_SUCCESS = f"{INFO}: [{error_prefix}] Bulk detokenize completed."

        PROCESSING_BATCHES = f"{INFO}: [{error_prefix}] Processing batches."

    class ErrorLogs(Enum):
        INSERT_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Insert call resulted in failure."
        GET_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Get call resulted in failure."
        UPDATE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Update call resulted in failure."
        DELETE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Delete call resulted in failure."
        DETOKENIZE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Detokenize call resulted in failure."
        QUERY_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Query call resulted in failure."
        BULK_INSERT_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Bulk insert batch resulted in failure."
        BULK_DETOKENIZE_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Bulk detokenize batch resulted in failure."
