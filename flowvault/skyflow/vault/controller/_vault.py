import json

from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import SKY_META_DATA_HEADER
from common.utils.logger import log_info, log_error_log
from common.vault.base_vault_controller import BaseVaultController
from skyflow.generated.rest import (
    ColumnRedactions,
    GetRequestData,
    InsertRecordData,
    TokenGroupRedactions as WireTokenGroupRedactions,
    UniqueValue,
    UpdateRecordData,
    Upsert,
)
from skyflow.generated.rest.core import ApiError, ParsingError
from skyflow.utils import SkyflowMessages, get_metrics
from skyflow.utils.enums import UpsertType
from skyflow.utils._response_parsing import parse_tokens, parse_hashed_data, parse_metadata
from skyflow.utils.validations import (
    validate_insert_request,
    validate_get_request,
    validate_update_request,
    validate_delete_request,
    validate_detokenize_request,
)
from skyflow.vault.data import (
    InsertRequest,
    InsertResponse,
    InsertResponseRecord,
    GetRequest,
    GetResponse,
    GetResponseRecord,
    UpdateRequest,
    UpdateResponse,
    UpdateResponseRecord,
    DeleteRequest,
    DeleteResponse,
    DeleteResponseRecord,
    DetokenizeRequest,
    DetokenizeResponse,
    DetokenizeResponseRecord,
    InsertOptions,
    GetOptions,
    UpdateOptions,
    DeleteOptions,
    DetokenizeOptions,
    RequestContext,
)

REQUEST_ID_HEADER = "x-request-id"
ADDITIONAL_HEADERS_KEY = "additional_headers"
UNKNOWN_ERROR_MESSAGE = "Unknown error"
OPERATION_INSERT = "INSERT"
OPERATION_GET = "GET"
OPERATION_UPDATE = "UPDATE"
OPERATION_DELETE = "DELETE"
OPERATION_DETOKENIZE = "DETOKENIZE"


class VaultController(BaseVaultController):
    _skyflow_messages = SkyflowMessages

    def __init__(self, vault_client):
        super().__init__(vault_client)

    def insert(self, request: InsertRequest, options: InsertOptions = None) -> InsertResponse:
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self._vault_client.get_logger())
        validate_insert_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table_name)
        for record in request.records:
            self._validate_table_name_if_present(record.table_name)
            self._validate_field_values(record.data)
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        records_api = self._vault_client.get_records_api()

        needs_per_record_table = any(r.table_name is not None for r in request.records)
        needs_per_record_upsert = any(r.upsert is not None for r in request.records)

        wire_records = [
            self.__build_wire_record(record, request, needs_per_record_table, needs_per_record_upsert)
            for record in request.records
        ]

        try:
            log_info(SkyflowMessages.Info.INSERT_TRIGGERED.value, self._vault_client.get_logger())
            upsert_kwargs = self.__omit_none(
                upsert=None if needs_per_record_upsert else self.__to_upsert(request.upsert),
            )
            raw_response = records_api.with_raw_response.insert_records(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table_name,
                records=wire_records,
                request_options=self.__unary_request_options(OPERATION_INSERT, options),
                **upsert_kwargs,
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records = [
                InsertResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in (raw_response.data.records or [])
            ]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self._vault_client.get_logger())
            error_records, request_id = self.__unary_error_records(e)
            if error_records is None:
                raise self.__to_skyflow_error(e)
            records = [
                InsertResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in error_records
            ]

        log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self._vault_client.get_logger())
        return InsertResponse(records=records)

    def get(self, request: GetRequest, options: GetOptions = None) -> GetResponse:
        log_info(SkyflowMessages.Info.VALIDATE_GET_REQUEST.value, self._vault_client.get_logger())
        validate_get_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table_name)
        log_info(SkyflowMessages.Info.GET_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        records_api = self._vault_client.get_records_api()

        if request.records is not None:
            call_kwargs = {'records': self.__to_get_request_data(request.records)}
            error_count = len(request.records)
        else:
            call_kwargs = {
                'table_name': request.table_name,
                'skyflow_i_ds': request.skyflow_ids,
                'unique_values': self.__to_unique_values(request.unique_values),
                'columns': request.columns,
                'column_redactions': self.__to_column_redactions(request.column_redactions),
                'limit': request.limit,
                'offset': request.offset,
            }
            error_count = len(request.skyflow_ids or request.unique_values or [])

        try:
            log_info(SkyflowMessages.Info.GET_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = records_api.with_raw_response.get_records(
                vault_id=self._vault_client.get_vault_id(),
                request_options=self.__unary_request_options(OPERATION_GET, options),
                **call_kwargs,
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records = [
                GetResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in (raw_response.data.records or [])
            ]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_RECORDS_REJECTED.value, self._vault_client.get_logger())
            error_records, request_id = self.__unary_error_records(e)
            if error_records is None:
                raise self.__to_skyflow_error(e)
            records = [
                GetResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in error_records
            ]

        log_info(SkyflowMessages.Info.GET_SUCCESS.value, self._vault_client.get_logger())
        return GetResponse(records=records)

    def update(self, request: UpdateRequest, options: UpdateOptions = None) -> UpdateResponse:
        log_info(SkyflowMessages.Info.VALIDATE_UPDATE_REQUEST.value, self._vault_client.get_logger())
        validate_update_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table_name)
        for record in request.records:
            self._validate_table_name_if_present(record.table_name)
            if record.data is not None:
                self._validate_field_values(record.data)
        log_info(SkyflowMessages.Info.UPDATE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        records_api = self._vault_client.get_records_api()

        try:
            needs_per_record_table = any(r.table_name is not None for r in request.records)

            wire_records = [
                self.__build_update_wire_record(record, request, needs_per_record_table)
                for record in request.records
            ]

            log_info(SkyflowMessages.Info.UPDATE_TRIGGERED.value, self._vault_client.get_logger())
            update_type_kwargs = self.__omit_none(update_type=self.__to_update_type(request.update_type))
            raw_response = records_api.with_raw_response.update_records(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table_name,
                records=wire_records,
                request_options=self.__unary_request_options(OPERATION_UPDATE, options),
                **update_type_kwargs,
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records = [
                UpdateResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in (raw_response.data.records or [])
            ]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.UPDATE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            error_records, request_id = self.__unary_error_records(e)
            if error_records is None:
                raise self.__to_skyflow_error(e)
            records = [
                UpdateResponseRecord(**self.__record_kwargs(record, include_data=True, request_id=request_id))
                for record in error_records
            ]

        log_info(SkyflowMessages.Info.UPDATE_SUCCESS.value, self._vault_client.get_logger())
        return UpdateResponse(records=records)

    def delete(self, request: DeleteRequest, options: DeleteOptions = None) -> DeleteResponse:
        log_info(SkyflowMessages.Info.VALIDATE_DELETE_REQUEST.value, self._vault_client.get_logger())
        validate_delete_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table_name)
        log_info(SkyflowMessages.Info.DELETE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        records_api = self._vault_client.get_records_api()
        items = request.ids or request.unique_values or []

        try:
            log_info(SkyflowMessages.Info.DELETE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = records_api.with_raw_response.delete_records(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table_name,
                skyflow_i_ds=request.ids,
                unique_values=self.__to_unique_values(request.unique_values),
                request_options=self.__unary_request_options(OPERATION_DELETE, options),
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records = [self.__delete_row(record, request_id) for record in (raw_response.data.records or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            error_records, request_id = self.__unary_error_records(e)
            if error_records is None:
                raise self.__to_skyflow_error(e)
            records = [self.__delete_row(record, request_id) for record in error_records]

        log_info(SkyflowMessages.Info.DELETE_SUCCESS.value, self._vault_client.get_logger())
        return DeleteResponse(records=records)

    def detokenize(self, request: DetokenizeRequest, options: DetokenizeOptions = None) -> DetokenizeResponse:
        log_info(SkyflowMessages.Info.VALIDATE_DETOKENIZE_REQUEST.value, self._vault_client.get_logger())
        validate_detokenize_request(self._vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DETOKENIZE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        tokens_api = self._vault_client.get_tokens_api()

        try:
            log_info(SkyflowMessages.Info.DETOKENIZE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = tokens_api.with_raw_response.detokenize(
                vault_id=self._vault_client.get_vault_id(),
                tokens=request.tokens,
                token_group_redactions=self.__to_token_group_redactions(request.token_group_redactions),
                request_options=self.__unary_request_options(OPERATION_DETOKENIZE, options),
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records = [self.__detokenize_row(resp, request_id) for resp in (raw_response.data.response or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            error_records, request_id = self.__unary_error_records(e)
            if error_records is None:
                raise self.__to_skyflow_error(e)
            records = [self.__detokenize_row(resp, request_id) for resp in error_records]

        log_info(SkyflowMessages.Info.DETOKENIZE_SUCCESS.value, self._vault_client.get_logger())
        return DetokenizeResponse(records=records)

    def __error_body_records(self, e):
        body = getattr(e, 'body', None)
        if isinstance(body, dict):
            records = body.get('records')
            if records is None:
                records = body.get('response')
        else:
            records = getattr(body, 'records', None) or getattr(body, 'response', None)
            if records is None:
                extra = getattr(body, '__pydantic_extra__', None)
                if isinstance(extra, dict):
                    records = extra.get('records') or extra.get('response')
        return records if isinstance(records, list) and records else None

    def __unary_error_records(self, e):
        records = self.__error_body_records(e)
        if not records:
            return None, None
        return records, self.__extract_request_id(getattr(e, 'headers', None))

    def __wire_record_value(self, record, wire_key, attr):
        if isinstance(record, dict):
            return record.get(wire_key)
        return getattr(record, attr, None)

    def __build_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return InsertRecordData(data=record.data, **self.__omit_none(
            tokens=record.tokens,
            table_name=(record.table_name or request.table_name) if needs_per_record_table else None,
            upsert=self.__to_upsert(record.upsert or request.upsert) if needs_per_record_upsert else None,
        ))

    def __build_update_wire_record(self, record, request, needs_per_record_table):
        return UpdateRecordData(
            skyflow_id=record.skyflow_id,
            data=record.data,
            **self.__omit_none(
                tokens=record.tokens,
                table_name=(record.table_name or request.table_name) if needs_per_record_table else None,
            ),
        )

    def __omit_none(self, **kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

    def __to_update_type(self, update_type):
        if update_type is None:
            return None
        return update_type.value if isinstance(update_type, UpsertType) else update_type

    def __build_headers(self):
        headers = {SKY_META_DATA_HEADER: json.dumps(get_metrics())}
        token = self._vault_client.get_current_bearer_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def __request_options(self, custom_headers=None):
        headers = self.__build_headers()
        if custom_headers:
            headers.update(custom_headers)
        return {ADDITIONAL_HEADERS_KEY: headers}

    def __unary_request_options(self, operation, options):
        interceptor = options.interceptor if options is not None else None
        custom_headers = None
        if interceptor is not None:
            context = RequestContext(operation)
            interceptor(context)
            custom_headers = {str(key): value for key, value in context.headers.items()}
        return self.__request_options(custom_headers)

    def __to_upsert(self, upsert):
        if upsert is None:
            return None
        update_type = upsert.update_type
        return Upsert(
            update_type=update_type.value if update_type else None,
            unique_columns=upsert.unique_columns,
        )

    def __to_unique_values(self, unique_values):
        if unique_values is None:
            return None
        return [UniqueValue(data=value) for value in unique_values]

    def __to_column_redactions(self, column_redactions):
        if column_redactions is None:
            return None
        return [
            ColumnRedactions(column_name=entry.column_name, redaction=entry.redaction)
            for entry in column_redactions
        ]

    def __to_token_group_redactions(self, token_group_redactions):
        if token_group_redactions is None:
            return None
        return [
            WireTokenGroupRedactions(token_group_name=entry.token_group_name, redaction=entry.redaction)
            for entry in token_group_redactions
        ]

    def __extract_request_id(self, headers):
        return headers.get(REQUEST_ID_HEADER) if headers else None

    def __record_kwargs(self, record, include_data, request_id=None):
        error = self.__wire_record_value(record, 'error', 'error')
        kwargs = {
            'table_name': self.__wire_record_value(record, 'tableName', 'table_name'),
            'skyflow_id': self.__wire_record_value(record, 'skyflowID', 'skyflow_id'),
            'tokens': parse_tokens(self.__wire_record_value(record, 'tokens', 'tokens')),
            'hashed_data': parse_hashed_data(self.__wire_record_value(record, 'hashedData', 'hashed_data')),
            'http_code': self.__wire_record_value(record, 'httpCode', 'http_code'),
            'error': error,
            'request_id': request_id if error is not None else None,
        }
        if include_data:
            kwargs['data'] = self.__wire_record_value(record, 'data', 'data')
        return kwargs

    def __to_skyflow_error(self, e):
        if isinstance(e, SkyflowError):
            return e
        if isinstance(e, (ApiError, ParsingError)):
            message, grpc_code, http_status, details = self.__parse_api_error_body(e.body)
            return SkyflowError(
                message=message,
                http_code=e.status_code,
                request_id=self.__extract_request_id(e.headers),
                grpc_code=grpc_code,
                http_status=http_status,
                details=details,
            )
        return SkyflowError(
            message=str(e) if e else CommonMessages.Error.GENERIC_API_ERROR.value,
            http_code=None,
        )

    def __parse_api_error_body(self, body):
        error = getattr(body, 'error', None) if body is not None and not isinstance(body, dict) else None
        if error is not None and not isinstance(error, dict):
            return (
                getattr(error, 'message', None) or UNKNOWN_ERROR_MESSAGE,
                getattr(error, 'grpc_code', None),
                getattr(error, 'http_status', None),
                getattr(error, 'details', None) or [],
            )
        if isinstance(body, dict):
            records = body.get('records')
            if isinstance(records, list) and records:
                first = records[0] if isinstance(records[0], dict) else {}
                message = first.get('error') or first.get('message') or UNKNOWN_ERROR_MESSAGE
                return (message, None, None, [record for record in records if isinstance(record, dict)])
            error = body.get('error')
            if isinstance(error, dict):
                return (
                    error.get('message') or UNKNOWN_ERROR_MESSAGE,
                    error.get('grpc_code', error.get('grpcCode')),
                    error.get('http_status', error.get('httpStatus')),
                    error.get('details') or [],
                )
            if error is not None:
                return (str(error), None, None, [])
        return (UNKNOWN_ERROR_MESSAGE, None, None, [])

    def __to_get_request_data(self, records):
        return [
            GetRequestData(
                table_name=record.table_name,
                skyflow_i_ds=record.skyflow_ids or [],
                **self.__omit_none(
                    columns=record.columns,
                    column_redactions=self.__to_column_redactions(record.column_redactions),
                    unique_values=self.__to_unique_values(record.unique_values),
                ),
            )
            for record in records
        ]

    def __delete_row(self, record, request_id=None):
        error = self.__wire_record_value(record, 'error', 'error')
        return DeleteResponseRecord(
            skyflow_id=self.__wire_record_value(record, 'skyflowID', 'skyflow_id'),
            http_code=self.__wire_record_value(record, 'httpCode', 'http_code'),
            error=error,
            request_id=request_id if error is not None else None,
        )

    def __detokenize_row(self, resp, request_id=None):
        error = self.__wire_record_value(resp, 'error', 'error')
        return DetokenizeResponseRecord(
            token=self.__wire_record_value(resp, 'token', 'token'),
            value=self.__wire_record_value(resp, 'value', 'value'),
            token_group_name=self.__wire_record_value(resp, 'tokenGroupName', 'token_group_name'),
            metadata=parse_metadata(self.__wire_record_value(resp, 'metadata', 'metadata')),
            http_code=self.__wire_record_value(resp, 'httpCode', 'http_code'),
            error=error,
            request_id=request_id if error is not None else None,
        )



