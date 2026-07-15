import json

from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import SKY_META_DATA_HEADER
from common.utils.logger import log_info, log_error_log
from common.vault.base_vault_controller import BaseVaultController
from skyflow_flowvault.generated.rest import (
    V1ColumnRedactions,
    V1FlowTokenizeRequestObject,
    V1InsertRecordData,
    V1TokenGroupRedactions,
    V1UniqueValue,
    V1UpdateRecordData,
    V1Upsert,
)
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.utils import SkyflowMessages, get_metrics
from skyflow_flowvault.utils.validations import (
    validate_insert_request,
    validate_get_request,
    validate_update_request,
    validate_delete_request,
    validate_detokenize_request,
    validate_tokenize_request,
)
from skyflow_flowvault.vault.data import (
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
    TokenizeRequest,
    TokenizeResponse,
)

REQUEST_ID_HEADER = "x-request-id"


class VaultController(BaseVaultController):
    _skyflow_messages = SkyflowMessages

    def __init__(self, vault_client):
        super().__init__(vault_client)

    def insert(self, request: InsertRequest) -> InsertResponse:
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self._vault_client.get_logger())
        validate_insert_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table)
        for record in request.values:
            self._validate_table_name_if_present(record.get("table"))
            self._validate_field_values(record.get("values"))
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        insert_api = self._vault_client.get_flowservice_api()

        needs_per_record_table = any(r.get("table") is not None for r in request.values)
        needs_per_record_upsert = any(r.get("upsert") is not None for r in request.values)

        wire_records = [
            self.__build_wire_record(record, request, needs_per_record_table, needs_per_record_upsert)
            for record in request.values
        ]

        try:
            log_info(SkyflowMessages.Info.INSERT_TRIGGERED.value, self._vault_client.get_logger())
            headers = self.__build_headers()
            top_level_kwargs = self.__omit_none(
                table_name=None if needs_per_record_table else request.table,
                upsert=None if needs_per_record_upsert else self.__to_v1_upsert(request.upsert),
            )
            raw_response = insert_api.with_raw_response.insert(
                vault_id=self._vault_client.get_vault_id(),
                records=wire_records,
                request_options={'additional_headers': headers},
                **top_level_kwargs,
            )
            request_id = self.__extract_request_id(raw_response.headers)
            inserted_fields, errors = self.__split_success_and_errors(raw_response.data.records or [], 0, request_id)
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self._vault_client.get_logger())
            inserted_fields, errors = [], self.__errors_from_exception(e, request.values, 0)

        log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self._vault_client.get_logger())
        return InsertResponse(inserted_fields=inserted_fields, errors=errors if errors else None)

    def get(self, request: GetRequest) -> GetResponse:
        log_info(SkyflowMessages.Info.VALIDATE_GET_REQUEST.value, self._vault_client.get_logger())
        validate_get_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table)
        log_info(SkyflowMessages.Info.GET_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        flowservice_api = self._vault_client.get_flowservice_api()
        items = request.ids or request.unique_values or []

        try:
            log_info(SkyflowMessages.Info.GET_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = flowservice_api.with_raw_response.get(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table,
                skyflow_i_ds=request.ids,
                unique_values=self.__to_v1_unique_values(request.unique_values),
                columns=request.columns,
                column_redactions=self.__to_v1_column_redactions(request.column_redactions),
                limit=request.limit,
                offset=request.offset,
                request_options={'additional_headers': self.__build_headers()},
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_success_and_errors(
                raw_response.data.records or [], 0, request_id, include_data=True,
            )
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_RECORDS_REJECTED.value, self._vault_client.get_logger())
            records, errors = [], self.__errors_from_exception(e, items, 0)

        log_info(SkyflowMessages.Info.GET_SUCCESS.value, self._vault_client.get_logger())
        return GetResponse(records=records, errors=errors if errors else None)

    def update(self, request: UpdateRequest) -> UpdateResponse:
        log_info(SkyflowMessages.Info.VALIDATE_UPDATE_REQUEST.value, self._vault_client.get_logger())
        validate_update_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table)
        for record in request.records:
            self._validate_table_name_if_present(record.get("table"))
            if record.get("values") is not None:
                self._validate_field_values(record.get("values"))
        log_info(SkyflowMessages.Info.UPDATE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        flowservice_api = self._vault_client.get_flowservice_api()

        needs_per_record_table = any(r.get("table") is not None for r in request.records)

        wire_records = [
            self.__build_update_wire_record(record, request, needs_per_record_table)
            for record in request.records
        ]

        try:
            log_info(SkyflowMessages.Info.UPDATE_TRIGGERED.value, self._vault_client.get_logger())
            top_level_kwargs = self.__omit_none(
                table_name=None if needs_per_record_table else request.table,
                update_type=request.update_type.value if request.update_type else None,
            )
            raw_response = flowservice_api.with_raw_response.update(
                vault_id=self._vault_client.get_vault_id(),
                records=wire_records,
                request_options={'additional_headers': self.__build_headers()},
                **top_level_kwargs,
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_success_and_errors(
                raw_response.data.records or [], 0, request_id, include_data=True,
            )
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.UPDATE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            records, errors = [], self.__errors_from_exception(e, request.records, 0)

        log_info(SkyflowMessages.Info.UPDATE_SUCCESS.value, self._vault_client.get_logger())
        return UpdateResponse(records=records, errors=errors if errors else None)

    def delete(self, request: DeleteRequest) -> DeleteResponse:
        log_info(SkyflowMessages.Info.VALIDATE_DELETE_REQUEST.value, self._vault_client.get_logger())
        validate_delete_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table)
        log_info(SkyflowMessages.Info.DELETE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        flowservice_api = self._vault_client.get_flowservice_api()
        items = request.ids or request.unique_values or []

        try:
            log_info(SkyflowMessages.Info.DELETE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = flowservice_api.with_raw_response.delete(
                vault_id=self._vault_client.get_vault_id(),
                table_name=request.table,
                skyflow_i_ds=request.ids,
                unique_values=self.__to_v1_unique_values(request.unique_values),
                request_options={'additional_headers': self.__build_headers()},
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_success_and_errors(raw_response.data.records or [], 0, request_id)
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            records, errors = [], self.__errors_from_exception(e, items, 0)

        log_info(SkyflowMessages.Info.DELETE_SUCCESS.value, self._vault_client.get_logger())
        return DeleteResponse(records=records, errors=errors if errors else None)

    def query(self, request):
        raise NotImplementedError("VaultController.query is not implemented yet")

    def detokenize(self, request: DetokenizeRequest) -> DetokenizeResponse:
        log_info(SkyflowMessages.Info.VALIDATE_DETOKENIZE_REQUEST.value, self._vault_client.get_logger())
        validate_detokenize_request(self._vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DETOKENIZE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        flowservice_api = self._vault_client.get_flowservice_api()

        try:
            log_info(SkyflowMessages.Info.DETOKENIZE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = flowservice_api.with_raw_response.detokenize(
                vault_id=self._vault_client.get_vault_id(),
                tokens=request.tokens,
                token_group_redactions=self.__to_v1_token_group_redactions(request.token_group_redactions),
                request_options={'additional_headers': self.__build_headers()},
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_detokenize_success_and_errors(raw_response.data.response or [], 0, request_id)
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            records, errors = [], self.__errors_from_exception(e, request.tokens, 0)

        log_info(SkyflowMessages.Info.DETOKENIZE_SUCCESS.value, self._vault_client.get_logger())
        return DetokenizeResponse(records=records, errors=errors if errors else None)

    def tokenize(self, request: TokenizeRequest) -> TokenizeResponse:
        log_info(SkyflowMessages.Info.VALIDATE_TOKENIZE_REQUEST.value, self._vault_client.get_logger())
        validate_tokenize_request(self._vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.TOKENIZE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        flowservice_api = self._vault_client.get_flowservice_api()

        wire_values = [self.__build_tokenize_wire_value(value) for value in request.values]

        try:
            log_info(SkyflowMessages.Info.TOKENIZE_TRIGGERED.value, self._vault_client.get_logger())
            raw_response = flowservice_api.with_raw_response.tokenize(
                vault_id=self._vault_client.get_vault_id(),
                data=wire_values,
                request_options={'additional_headers': self.__build_headers()},
            )
            request_id = self.__extract_request_id(raw_response.headers)
            records, errors = self.__split_tokenize_success_and_errors(raw_response.data.response or [], 0, request_id)
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.TOKENIZE_RECORDS_REJECTED.value, self._vault_client.get_logger())
            records, errors = [], self.__errors_from_exception(e, request.values, 0)

        log_info(SkyflowMessages.Info.TOKENIZE_SUCCESS.value, self._vault_client.get_logger())
        return TokenizeResponse(records=records, errors=errors if errors else None)

    def __build_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return V1InsertRecordData(data=record["values"], **self.__omit_none(
            table_name=(record.get("table") or request.table) if needs_per_record_table else None,
            upsert=self.__to_v1_upsert(record.get("upsert") or request.upsert) if needs_per_record_upsert else None,
        ))

    def __build_update_wire_record(self, record, request, needs_per_record_table):
        return V1UpdateRecordData(
            skyflow_id=record.get("skyflow_id"),
            data=record.get("values"),
            **self.__omit_none(
                tokens=record.get("tokens"),
                table_name=(record.get("table") or request.table) if needs_per_record_table else None,
            ),
        )

    def __build_tokenize_wire_value(self, value):
        return V1FlowTokenizeRequestObject(
            value=value.get("value"),
            token_group_names=value.get("token_group_names"),
            **self.__omit_none(token=value.get("token")),
        )

    def __omit_none(self, **kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

    def __build_headers(self):
        headers = {SKY_META_DATA_HEADER: json.dumps(get_metrics())}
        token = self._vault_client.get_current_bearer_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def __to_v1_upsert(self, upsert):
        if upsert is None:
            return None
        update_type = upsert.get("update_type")
        return V1Upsert(
            update_type=update_type.value if update_type else None,
            unique_columns=upsert.get("unique_columns"),
        )

    def __to_v1_unique_values(self, unique_values):
        if unique_values is None:
            return None
        return [V1UniqueValue(data=value) for value in unique_values]

    def __to_v1_column_redactions(self, column_redactions):
        if column_redactions is None:
            return None
        return [
            V1ColumnRedactions(column_name=entry.get("column_name"), redaction=entry.get("redaction"))
            for entry in column_redactions
        ]

    def __to_v1_token_group_redactions(self, token_group_redactions):
        if token_group_redactions is None:
            return None
        return [
            V1TokenGroupRedactions(token_group_name=entry.get("token_group_name"), redaction=entry.get("redaction"))
            for entry in token_group_redactions
        ]

    def __extract_request_id(self, headers):
        return headers.get(REQUEST_ID_HEADER) if headers else None

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

    def __split_detokenize_success_and_errors(self, responses, start_index, request_id):
        successes, errors = [], []
        for offset, resp in enumerate(responses):
            request_index = start_index + offset
            if resp.error is not None:
                errors.append({
                    'request_index': request_index, 'token': resp.token, 'error': resp.error,
                    'code': resp.http_code, 'request_id': request_id,
                })
            else:
                successes.append({
                    'request_index': request_index,
                    'token': resp.token,
                    'value': resp.value,
                    'token_group_name': resp.token_group_name,
                })
        return successes, errors

    def __split_tokenize_success_and_errors(self, responses, start_index, request_id):
        successes, errors = [], []
        for offset, resp in enumerate(responses):
            request_index = start_index + offset
            for token in (resp.tokens or []):
                if token.error is not None:
                    errors.append({
                        'request_index': request_index, 'token_group_name': token.token_group_name,
                        'error': token.error, 'code': token.http_code, 'request_id': request_id,
                    })
                else:
                    successes.append({
                        'request_index': request_index,
                        'value': resp.value,
                        'token_group_name': token.token_group_name,
                        'token': token.token,
                    })
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

    def __errors_from_exception(self, e, records, start_index):
        if isinstance(e, ApiError):
            request_id = self.__extract_request_id(e.headers)
            body = e.body if isinstance(e.body, dict) else None
            if body and isinstance(body.get('records'), list) and body['records']:
                return [
                    self.__error_dict_from_record_map(record, start_index + offset, request_id)
                    for offset, record in enumerate(body['records']) if isinstance(record, dict)
                ]
            if body and body.get('error') is not None:
                err_field = body['error']
                if isinstance(err_field, dict):
                    return [self.__error_dict_from_record_map(err_field, start_index + i, request_id) for i in range(len(records))]
                return [{'request_index': start_index + i, 'error': str(err_field), 'code': e.status_code, 'request_id': request_id}
                        for i in range(len(records))]
            return [{'request_index': start_index + i, 'error': str(e), 'code': e.status_code, 'request_id': request_id}
                    for i in range(len(records))]
        message = str(e) if e else CommonMessages.Error.GENERIC_API_ERROR.value
        return [{'request_index': start_index + i, 'error': message, 'code': None, 'request_id': None} for i in range(len(records))]

    def __error_dict_from_record_map(self, record_map, request_index, request_id):
        code = record_map.get('http_code', record_map.get('httpCode', record_map.get('statusCode')))
        message = record_map.get('error', record_map.get('message', 'Unknown error'))
        return {'request_index': request_index, 'error': message, 'code': code, 'request_id': request_id}
