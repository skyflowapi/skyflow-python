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
        EMPTY_RECORDS_IN_INSERT = f"{error_prefix} Insert failed. Specify at least one record to insert."
        INVALID_RECORDS_TYPE_IN_INSERT = f"{error_prefix} Insert failed. 'records' must be a list of dicts."
        INVALID_RECORD_DATA_IN_INSERT = f"{error_prefix} Insert failed. Each record's 'values' must be a non-empty dict."
        INVALID_TABLE_NAME_IN_INSERT = f"{error_prefix} Insert failed. 'table' must be a non-empty string."
        INVALID_UPSERT_TYPE_IN_INSERT = f"{error_prefix} Insert failed. 'upsert' must be a dict."
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
        EMPTY_KEY_IN_INSERT_DATA = f"{error_prefix} Insert failed. Each record's 'values' must not contain a null or empty key."
        EMPTY_VALUE_IN_INSERT_DATA = f"{error_prefix} Insert failed. Each record's 'values' must not contain a null or empty value."

    class Info(Enum):
        VALIDATE_INSERT_REQUEST = f"{INFO}: [{error_prefix}] Validating insert request."
        INSERT_TRIGGERED = f"{INFO}: [{error_prefix}] Insert method triggered."
        INSERT_REQUEST_RESOLVED = f"{INFO}: [{error_prefix}] Insert request resolved."
        INSERT_SUCCESS = f"{INFO}: [{error_prefix}] Data inserted."

    class ErrorLogs(Enum):
        INSERT_RECORDS_REJECTED = f"{ERROR}: [{error_prefix}] Insert call resulted in failure."
