import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial

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
from skyflow.generated.rest.core import ApiError
from skyflow.utils import SkyflowMessages, get_metrics
from skyflow.utils._response_parsing import parse_tokens, parse_hashed_data, parse_metadata
from skyflow.utils._batching import (
    resolve_batch_config,
    create_batches,
    INSERT_BATCH_SIZE_KEY,
    INSERT_CONCURRENCY_LIMIT_KEY,
    DETOKENIZE_BATCH_SIZE_KEY,
    DETOKENIZE_CONCURRENCY_LIMIT_KEY,
)
from skyflow.utils.validations import (
    validate_insert_request,
    validate_get_request,
    validate_update_request,
    validate_delete_request,
    validate_detokenize_request,
    validate_query_request,
    validate_bulk_insert_request,
    validate_bulk_detokenize_request,
)
from skyflow.vault.data import (
    InsertRequest,
    InsertResponse,
    GetRequest,
    GetResponse,
    UpdateRequest,
    UpdateResponse,
    DeleteRequest,
    DeleteResponse,
    DetokenizeRequest,
    DetokenizeResponse,
    QueryRequest,
    QueryResponse,
    BulkInsertRequest,
    BulkInsertResponse,
    BulkSummary,
    BulkDetokenizeRequest,
    BulkDetokenizeResponse,
    DetokenizeSummary,
    BulkInsertOptions,
    BulkDetokenizeOptions,
    RequestContext,
)

REQUEST_ID_HEADER = "x-request-id"
ADDITIONAL_HEADERS_KEY = "additional_headers"
UNKNOWN_ERROR_MESSAGE = "Unknown error"
OPERATION_INSERT = "INSERT"
OPERATION_DETOKENIZE = "DETOKENIZE"


class VaultController(BaseVaultController):
    _skyflow_messages = SkyflowMessages

    def __init__(self, vault_client):
        super().__init__(vault_client)

    def insert(self, request: InsertRequest) -> InsertResponse:
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
                request_options=self.__request_options(),
                **upsert_kwargs,
            )
            records = [self.__record_row(record, include_data=False) for record in (raw_response.data.records or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self._vault_client.get_logger())
        return InsertResponse(records=records)

    def get(self, request: GetRequest) -> GetResponse:
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
                'skyflow_i_ds': request.ids,
                'unique_values': self.__to_unique_values(request.unique_values),
                'columns': request.columns,
                'column_redactions': self.__to_column_redactions(request.column_redactions),
                'limit': request.limit,
                'offset': request.offset,
            }
            error_count = len(request.ids or request.unique_values or [])

        try:
            log_info(SkyflowMessages.Info.GET_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = records_api.with_raw_response.get_records(
                vault_id=self._vault_client.get_vault_id(),
                request_options=self.__request_options(),
                **call_kwargs,
            )
            records = [self.__record_row(record, include_data=True) for record in (raw_response.data.records or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.GET_SUCCESS.value, self._vault_client.get_logger())
        return GetResponse(records=records)

    def update(self, request: UpdateRequest) -> UpdateResponse:
        log_info(SkyflowMessages.Info.VALIDATE_UPDATE_REQUEST.value, self._vault_client.get_logger())
        validate_update_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table_name)
        for record in request.records:
            self._validate_table_name_if_present(record.get("table_name"))
            if record.get("data") is not None:
                self._validate_field_values(record.get("data"))
        log_info(SkyflowMessages.Info.UPDATE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        records_api = self._vault_client.get_records_api()

        needs_per_record_table = any(r.get("table_name") is not None for r in request.records)

        wire_records = [
            self.__build_update_wire_record(record, request, needs_per_record_table)
            for record in request.records
        ]

        try:
            log_info(SkyflowMessages.Info.UPDATE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = records_api.with_raw_response.update_records(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table_name,
                records=wire_records,
                request_options=self.__request_options(),
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_success_and_errors(
                raw_response.data.records or [], 0, request_id, include_data=True,
            )
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.UPDATE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.UPDATE_SUCCESS.value, self._vault_client.get_logger())
        return UpdateResponse(records=records, errors=errors if errors else None)

    def delete(self, request: DeleteRequest) -> DeleteResponse:
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
                request_options=self.__request_options(),
            )
            records = [self.__delete_row(record) for record in (raw_response.data.records or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.DELETE_SUCCESS.value, self._vault_client.get_logger())
        return DeleteResponse(records=records)

    def query(self, request: QueryRequest) -> QueryResponse:
        log_info(SkyflowMessages.Info.VALIDATE_QUERY_REQUEST.value, self._vault_client.get_logger())
        validate_query_request(self._vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.QUERY_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        query_api = self._vault_client.get_query_api()

        try:
            log_info(SkyflowMessages.Info.QUERY_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = query_api.with_raw_response.execute_query(
                vault_id=self._vault_client.get_vault_id(),
                query=request.query,
                request_options=self.__request_options(),
            )
            records = [{'data': getattr(record, 'data', None)} for record in (raw_response.data.records or [])]
            metadata = self.__query_metadata(raw_response.data)
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.QUERY_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.QUERY_SUCCESS.value, self._vault_client.get_logger())
        return QueryResponse(records=records, metadata=metadata)

    def detokenize(self, request: DetokenizeRequest) -> DetokenizeResponse:
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
                request_options=self.__request_options(),
            )
            records = [self.__detokenize_row(resp) for resp in (raw_response.data.response or [])]
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            raise self.__to_skyflow_error(e)

        log_info(SkyflowMessages.Info.DETOKENIZE_SUCCESS.value, self._vault_client.get_logger())
        return DetokenizeResponse(records=records)

    def bulk_insert(self, request: BulkInsertRequest, options: BulkInsertOptions = None) -> BulkInsertResponse:
        batches, concurrency, top_kwargs = self.__prepare_bulk_insert(request)
        interceptor = options.interceptor if options is not None else None
        records_api = self._vault_client.get_records_api()
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.BULK_INSERT_TRIGGERED.value, logger)

        def call_batch(batch, start_index, batch_index, total_batches):
            try:
                raw_response = records_api.with_raw_response.insert_records(
                    vault_id=self._vault_client.get_vault_id(),
                    table_name=request.table_name,
                    records=batch,
                    request_options=self.__bulk_request_options(OPERATION_INSERT, batch_index, total_batches, interceptor),
                    **top_kwargs,
                )
                return self.__format_bulk_insert_batch(raw_response.data.records or [], start_index, raw_response.headers)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.BULK_INSERT_RECORDS_REJECTED.value, logger)
                return self.__bulk_insert_batch_error_rows(e, len(batch), start_index)

        records = self.__run_batches_sync(batches, call_batch, concurrency)
        log_info(SkyflowMessages.Info.BULK_INSERT_SUCCESS.value, logger)
        return self.__build_bulk_insert_response(records, request.records)

    async def bulk_insert_async(self, request: BulkInsertRequest, options: BulkInsertOptions = None) -> BulkInsertResponse:
        batches, concurrency, top_kwargs = self.__prepare_bulk_insert(request)
        interceptor = options.interceptor if options is not None else None
        records_api = self._vault_client.get_async_records_api()
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.BULK_INSERT_TRIGGERED.value, logger)

        async def call_batch(batch, start_index, batch_index, total_batches):
            try:
                raw_response = await records_api.with_raw_response.insert_records(
                    vault_id=self._vault_client.get_vault_id(),
                    table_name=request.table_name,
                    records=batch,
                    request_options=self.__bulk_request_options(OPERATION_INSERT, batch_index, total_batches, interceptor),
                    **top_kwargs,
                )
                return self.__format_bulk_insert_batch(raw_response.data.records or [], start_index, raw_response.headers)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.BULK_INSERT_RECORDS_REJECTED.value, logger)
                return self.__bulk_insert_batch_error_rows(e, len(batch), start_index)

        records = await self.__run_batches_async(batches, call_batch, concurrency)
        log_info(SkyflowMessages.Info.BULK_INSERT_SUCCESS.value, logger)
        return self.__build_bulk_insert_response(records, request.records)

    def bulk_detokenize(self, request: BulkDetokenizeRequest, options: BulkDetokenizeOptions = None) -> BulkDetokenizeResponse:
        batches, concurrency, redactions = self.__prepare_bulk_detokenize(request)
        interceptor = options.interceptor if options is not None else None
        tokens_api = self._vault_client.get_tokens_api()
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.BULK_DETOKENIZE_TRIGGERED.value, logger)

        def call_batch(batch, start_index, batch_index, total_batches):
            try:
                raw_response = tokens_api.with_raw_response.detokenize(
                    vault_id=self._vault_client.get_vault_id(),
                    tokens=batch,
                    token_group_redactions=redactions,
                    request_options=self.__bulk_request_options(OPERATION_DETOKENIZE, batch_index, total_batches, interceptor),
                )
                return self.__format_bulk_detokenize_batch(raw_response.data.response or [], start_index, raw_response.headers)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.BULK_DETOKENIZE_RECORDS_REJECTED.value, logger)
                return self.__bulk_detokenize_batch_error_rows(e, len(batch), start_index)

        records = self.__run_batches_sync(batches, call_batch, concurrency)
        log_info(SkyflowMessages.Info.BULK_DETOKENIZE_SUCCESS.value, logger)
        return self.__build_bulk_detokenize_response(records, request.tokens)

    async def bulk_detokenize_async(self, request: BulkDetokenizeRequest, options: BulkDetokenizeOptions = None) -> BulkDetokenizeResponse:
        batches, concurrency, redactions = self.__prepare_bulk_detokenize(request)
        interceptor = options.interceptor if options is not None else None
        tokens_api = self._vault_client.get_async_tokens_api()
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.BULK_DETOKENIZE_TRIGGERED.value, logger)

        async def call_batch(batch, start_index, batch_index, total_batches):
            try:
                raw_response = await tokens_api.with_raw_response.detokenize(
                    vault_id=self._vault_client.get_vault_id(),
                    tokens=batch,
                    token_group_redactions=redactions,
                    request_options=self.__bulk_request_options(OPERATION_DETOKENIZE, batch_index, total_batches, interceptor),
                )
                return self.__format_bulk_detokenize_batch(raw_response.data.response or [], start_index, raw_response.headers)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.BULK_DETOKENIZE_RECORDS_REJECTED.value, logger)
                return self.__bulk_detokenize_batch_error_rows(e, len(batch), start_index)

        records = await self.__run_batches_async(batches, call_batch, concurrency)
        log_info(SkyflowMessages.Info.BULK_DETOKENIZE_SUCCESS.value, logger)
        return self.__build_bulk_detokenize_response(records, request.tokens)

    def __prepare_bulk_insert(self, request):
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.VALIDATE_BULK_INSERT_REQUEST.value, logger)
        validate_bulk_insert_request(logger, request)
        self._validate_table_name_if_present(request.table_name)
        for record in request.records:
            self._validate_table_name_if_present(record.table_name)
            self._validate_field_values(record.data)
        log_info(SkyflowMessages.Info.BULK_INSERT_REQUEST_RESOLVED.value, logger)
        self._vault_client.initialize_client_configuration()

        batch_size, concurrency = resolve_batch_config(
            INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, len(request.records), logger,
        )
        needs_per_record_table = any(r.table_name is not None for r in request.records)
        needs_per_record_upsert = any(r.upsert is not None for r in request.records)
        wire_records = [
            self.__build_bulk_insert_wire_record(r, request, needs_per_record_table, needs_per_record_upsert)
            for r in request.records
        ]
        batches = self.__index_batches(wire_records, batch_size)
        top_kwargs = self.__omit_none(
            upsert=None if needs_per_record_upsert else self.__to_upsert(request.upsert),
        )
        log_info(SkyflowMessages.Info.PROCESSING_BATCHES.value, logger)
        return batches, concurrency, top_kwargs

    def __prepare_bulk_detokenize(self, request):
        logger = self._vault_client.get_logger()
        log_info(SkyflowMessages.Info.VALIDATE_BULK_DETOKENIZE_REQUEST.value, logger)
        validate_bulk_detokenize_request(logger, request)
        log_info(SkyflowMessages.Info.BULK_DETOKENIZE_REQUEST_RESOLVED.value, logger)
        self._vault_client.initialize_client_configuration()

        batch_size, concurrency = resolve_batch_config(
            DETOKENIZE_BATCH_SIZE_KEY, DETOKENIZE_CONCURRENCY_LIMIT_KEY, len(request.tokens), logger,
        )
        batches = self.__index_batches(request.tokens, batch_size)
        redactions = self.__to_token_group_redactions(request.token_group_redactions)
        log_info(SkyflowMessages.Info.PROCESSING_BATCHES.value, logger)
        return batches, concurrency, redactions

    def __index_batches(self, items, batch_size):
        batches = create_batches(items, batch_size)
        total_batches, start_index, indexed = len(batches), 0, []
        for batch_index, batch in enumerate(batches):
            indexed.append((batch, start_index, batch_index, total_batches))
            start_index += len(batch)
        return indexed

    def __run_batches_sync(self, batches, call_batch, concurrency):
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
            futures = [executor.submit(call_batch, *batch) for batch in batches]
            merged = []
            for future in futures:
                merged.extend(future.result())
        return merged

    async def __run_batches_async(self, batches, call_batch, concurrency):
        semaphore = asyncio.Semaphore(max(1, concurrency))

        async def guarded(batch):
            async with semaphore:
                return await call_batch(*batch)

        results = await asyncio.gather(*(guarded(batch) for batch in batches))
        merged = []
        for result in results:
            merged.extend(result)
        return merged

    def __build_bulk_insert_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return InsertRecordData(data=record.data, **self.__omit_none(
            tokens=record.tokens,
            table_name=(record.table_name or request.table_name) if needs_per_record_table else None,
            upsert=self.__to_upsert(record.upsert or request.upsert) if needs_per_record_upsert else None,
        ))

    def __format_bulk_insert_batch(self, records, start_index, headers):
        request_id = self.__extract_request_id(headers)
        rows = []
        for offset, record in enumerate(records):
            error = getattr(record, 'error', None)
            rows.append({
                'index': start_index + offset,
                'request_id': request_id if error is not None else None,
                'table_name': getattr(record, 'table_name', None),
                'skyflow_id': getattr(record, 'skyflow_id', None),
                'tokens': parse_tokens(getattr(record, 'tokens', None)),
                'hashed_data': parse_hashed_data(getattr(record, 'hashed_data', None)),
                'http_code': getattr(record, 'http_code', None),
                'error': error,
            })
        return rows

    def __format_bulk_detokenize_batch(self, responses, start_index, headers):
        request_id = self.__extract_request_id(headers)
        rows = []
        for offset, resp in enumerate(responses):
            error = getattr(resp, 'error', None)
            rows.append({
                'index': start_index + offset,
                'request_id': request_id if error is not None else None,
                'value': getattr(resp, 'value', None),
                'token_group_name': getattr(resp, 'token_group_name', None),
                'metadata': parse_metadata(getattr(resp, 'metadata', None)),
                'http_code': getattr(resp, 'http_code', None),
                'token': getattr(resp, 'token', None),
                'error': error,
            })
        return rows

    def __bulk_batch_error_tuples(self, e, count, start_index):
        if isinstance(e, ApiError):
            request_id = self.__extract_request_id(e.headers)
            status = e.status_code
            body = e.body if isinstance(e.body, dict) else None
            if body and isinstance(body.get('records'), list) and body['records']:
                tuples = [
                    (start_index + offset, request_id,
                     record.get('error', record.get('message', UNKNOWN_ERROR_MESSAGE)),
                     record.get('http_code', record.get('httpCode', record.get('statusCode', status))))
                    for offset, record in enumerate(body['records']) if isinstance(record, dict)
                ]
                if tuples:
                    return tuples
            message, _, _, _ = self.__parse_api_error_body(e.body)
            return [(start_index + i, request_id, message, status) for i in range(count)]
        message = str(e) if e else CommonMessages.Error.GENERIC_API_ERROR.value
        return [(start_index + i, None, message, None) for i in range(count)]

    def __bulk_insert_batch_error_rows(self, e, count, start_index):
        return [
            {'index': idx, 'request_id': request_id, 'table_name': None, 'skyflow_id': None,
             'tokens': None, 'hashed_data': None, 'http_code': code, 'error': message}
            for idx, request_id, message, code in self.__bulk_batch_error_tuples(e, count, start_index)
        ]

    def __bulk_detokenize_batch_error_rows(self, e, count, start_index):
        return [
            {'index': idx, 'request_id': request_id, 'value': None, 'token_group_name': None,
             'metadata': None, 'http_code': code, 'token': None, 'error': message}
            for idx, request_id, message, code in self.__bulk_batch_error_tuples(e, count, start_index)
        ]

    def __build_bulk_insert_response(self, records, original_records):
        total_failed = sum(1 for record in records if record.get('error') is not None)
        summary = BulkSummary(
            total_records=len(original_records),
            total_inserted=len(records) - total_failed,
            total_failed=total_failed,
        )
        return BulkInsertResponse(summary=summary, records=records, _original_records=original_records)

    def __build_bulk_detokenize_response(self, records, original_tokens):
        total_failed = sum(1 for record in records if record.get('error') is not None)
        summary = DetokenizeSummary(
            total_tokens=len(original_tokens),
            total_detokenized=len(records) - total_failed,
            total_failed=total_failed,
        )
        return BulkDetokenizeResponse(summary=summary, records=records, _original_tokens=original_tokens)

    def __build_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return InsertRecordData(data=record.data, **self.__omit_none(
            tokens=record.tokens,
            table_name=(record.table_name or request.table_name) if needs_per_record_table else None,
            upsert=self.__to_upsert(record.upsert or request.upsert) if needs_per_record_upsert else None,
        ))

    def __build_update_wire_record(self, record, request, needs_per_record_table):
        return UpdateRecordData(
            skyflow_id=record.get("skyflow_id"),
            data=record.get("data"),
            **self.__omit_none(
                table_name=(record.get("table_name") or request.table_name) if needs_per_record_table else None,
            ),
        )

    def __omit_none(self, **kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

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

    def __bulk_request_options(self, operation, batch_index, total_batches, interceptor):
        custom_headers = None
        if interceptor is not None:
            context = RequestContext(operation, batch_index, total_batches)
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

    def __record_row(self, record, include_data):
        row = {
            'table_name': getattr(record, 'table_name', None),
            'skyflow_id': getattr(record, 'skyflow_id', None),
            'tokens': parse_tokens(getattr(record, 'tokens', None)),
            'hashed_data': parse_hashed_data(getattr(record, 'hashed_data', None)),
            'http_code': getattr(record, 'http_code', None),
            'error': getattr(record, 'error', None),
        }
        if include_data:
            row['data'] = getattr(record, 'data', None)
        return row

    def __to_skyflow_error(self, e):
        if isinstance(e, SkyflowError):
            return e
        if isinstance(e, ApiError):
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
                skyflow_i_ds=record.ids or [],
                **self.__omit_none(
                    columns=record.columns,
                    column_redactions=self.__to_column_redactions(record.column_redactions),
                    unique_values=self.__to_unique_values(record.unique_values),
                ),
            )
            for record in records
        ]

    def __delete_row(self, record):
        return {
            'skyflow_id': getattr(record, 'skyflow_id', None),
            'http_code': getattr(record, 'http_code', None),
            'error': getattr(record, 'error', None),
        }

    def __detokenize_row(self, resp):
        return {
            'token': getattr(resp, 'token', None),
            'token_group_name': getattr(resp, 'token_group_name', None),
            'value': getattr(resp, 'value', None),
            'metadata': parse_metadata(getattr(resp, 'metadata', None)),
            'http_code': getattr(resp, 'http_code', None),
            'error': getattr(resp, 'error', None),
        }

    def __query_metadata(self, data):
        meta = getattr(data, 'metadata', None)
        if meta is None:
            return None
        return {'columns': getattr(meta, 'columns', None)}

    def __split_success_and_errors(self, records, start_index, request_id, include_data=False):
        successes, errors = [], []
        for offset, record in enumerate(records):
            request_index = start_index + offset
            if record.error is not None:
                errors.append({'request_index': request_index, 'error': record.error, 'code': record.http_code, 'request_id': request_id})
            else:
                success = {
                    'request_index': request_index,
                    'skyflow_id': record.skyflow_id,
                }
                success.update(self.__flatten_tokens(getattr(record, 'tokens', None)))
                if include_data:
                    data = getattr(record, 'data', None)
                    if data:
                        success['data'] = data
                    hashed_data = getattr(record, 'hashed_data', None)
                    if hashed_data:
                        success['hashed_data'] = hashed_data
                successes.append(success)
        return successes, errors

    def __flatten_tokens(self, tokens):
        if not tokens:
            return {}
        flat = {}
        for column, entries in tokens.items():
            if isinstance(entries, list):
                token_values = [entry.get('token') for entry in entries if isinstance(entry, dict)]
                flat[column] = token_values[0] if len(token_values) == 1 else token_values
            else:
                flat[column] = entries
        return flat

