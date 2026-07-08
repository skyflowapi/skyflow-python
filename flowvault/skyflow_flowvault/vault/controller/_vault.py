import json

from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import SKY_META_DATA_HEADER
from common.utils.logger import log_info, log_error_log
from common.vault.base_vault import BaseVaultController
from skyflow_flowvault.generated.rest import V1InsertRecordData, V1Upsert
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.utils import SkyflowMessages, get_metrics
from skyflow_flowvault.utils.validations import validate_insert_request
from skyflow_flowvault.vault.data import InsertResponse

REQUEST_ID_HEADER = "x-request-id"


class VaultController(BaseVaultController):
    _skyflow_messages = SkyflowMessages

    def __init__(self, vault_client):
        super().__init__(vault_client)

    def insert(self, request):
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self._vault_client.get_logger())
        validate_insert_request(self._vault_client.get_logger(), request)
        self._validate_table_name_if_present(request.table)
        for record in request.records:
            self._validate_table_name_if_present(record.get("table"))
            self._validate_field_values(record.get("values"))
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        insert_api = self._vault_client.get_insert_api()

        needs_per_record_table = any(r.get("table") is not None for r in request.records)
        needs_per_record_upsert = any(r.get("upsert") is not None for r in request.records)

        wire_records = [
            self.__build_wire_record(record, request, needs_per_record_table, needs_per_record_upsert)
            for record in request.records
        ]

        try:
            log_info(SkyflowMessages.Info.INSERT_TRIGGERED.value, self._vault_client.get_logger())
            headers = self.__build_headers()
            top_level_kwargs = self.__omit_none(
                table_name=None if needs_per_record_table else request.table,
                upsert=None if needs_per_record_upsert else self.__to_v1_upsert(request.upsert),
            )
            # with_raw_response so x-request-id is available to tag onto each result.
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
            inserted_fields, errors = [], self.__errors_from_exception(e, request.records, 0)

        log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self._vault_client.get_logger())
        return InsertResponse(inserted_fields=inserted_fields, errors=errors if errors else None)

    # Not built out this round (insert-only) -- stubs exist so this class stays instantiable
    # under BaseVaultController's abstract contract.
    def get(self, request):
        raise NotImplementedError("VaultController.get is not implemented yet")

    def update(self, request):
        raise NotImplementedError("VaultController.update is not implemented yet")

    def delete(self, request):
        raise NotImplementedError("VaultController.delete is not implemented yet")

    def query(self, request):
        raise NotImplementedError("VaultController.query is not implemented yet")

    def detokenize(self, request):
        raise NotImplementedError("VaultController.detokenize is not implemented yet")

    def __build_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return V1InsertRecordData(data=record["values"], **self.__omit_none(
            table_name=(record.get("table") or request.table) if needs_per_record_table else None,
            upsert=self.__to_v1_upsert(record.get("upsert") or request.upsert) if needs_per_record_upsert else None,
        ))

    def __omit_none(self, **kwargs):
        # A field explicitly passed as None still serializes as null; omitting the kwarg
        # entirely is what actually excludes it from the outgoing JSON.
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
        return V1Upsert(
            update_type=upsert.update_type.value if upsert.update_type else None,
            unique_columns=upsert.unique_columns,
        )

    def __extract_request_id(self, headers):
        return headers.get(REQUEST_ID_HEADER) if headers else None

    def __split_success_and_errors(self, records, start_index, request_id):
 
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
                success.update(self.__flatten_tokens(record.tokens))
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

    def __errors_from_exception(self, e, records, start_index):
        # Prefers a structured per-record error body over one flat message per batch.
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
