import json

from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import SKY_META_DATA_HEADER
from common.utils.logger import log_info, log_error_log
from common.vault.base_vault import VaultController
from skyflow_flowvault.generated.rest import V1InsertRecordData, V1Upsert
from skyflow_flowvault.generated.rest.core import ApiError
from skyflow_flowvault.utils import SkyflowMessages, get_metrics
from skyflow_flowvault.utils.validations import validate_insert_request
from skyflow_flowvault.vault.data import InsertResponse

REQUEST_ID_HEADER = "x-request-id"


class FlowVaultController(VaultController):
    def __init__(self, vault_client):
        super().__init__(vault_client)

    def insert(self, request):
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self._vault_client.get_logger())
        validate_insert_request(self._vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self._vault_client.get_logger())
        self._vault_client.initialize_client_configuration()

        insert_api = self._vault_client.get_insert_api()
        batch_size = self._get_insert_batch_size(self._vault_client.get_logger())

        def send_one_batch(batch_records, start_index):
            # table_name/upsert can't be set in both places at once (confirmed against a real
            # vault) -- if any record needs its own, every record gets a resolved value and the
            # top-level field is omitted; otherwise the top-level field carries it alone.
            needs_per_record_table = any(r.table is not None for r in batch_records)
            needs_per_record_upsert = any(r.upsert is not None for r in batch_records)

            wire_records = [
                self.__build_wire_record(record, request, needs_per_record_table, needs_per_record_upsert)
                for record in batch_records
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
                return self.__split_success_and_errors(raw_response.data.records or [], start_index, request_id)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self._vault_client.get_logger())
                return [], self.__errors_from_exception(e, batch_records, start_index)

        successes, errors = self._run_batches(request.records, batch_size, send_one_batch)
        log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self._vault_client.get_logger())
        summary = {
            'total_records': len(request.records),
            'total_inserted': len(successes),
            'total_failed': len(errors),
        }
        return InsertResponse(summary=summary, success=successes, errors=errors)

    # Not built out this round (insert-only) -- stubs exist so this class stays instantiable
    # under VaultController's abstract contract.
    def get(self, request):
        raise NotImplementedError("FlowVaultController.get is not implemented yet")

    def update(self, request):
        raise NotImplementedError("FlowVaultController.update is not implemented yet")

    def delete(self, request):
        raise NotImplementedError("FlowVaultController.delete is not implemented yet")

    def query(self, request):
        raise NotImplementedError("FlowVaultController.query is not implemented yet")

    def detokenize(self, request):
        raise NotImplementedError("FlowVaultController.detokenize is not implemented yet")

    def __build_wire_record(self, record, request, needs_per_record_table, needs_per_record_upsert):
        return V1InsertRecordData(data=record.data, **self.__omit_none(
            table_name=(record.table or request.table) if needs_per_record_table else None,
            upsert=self.__to_v1_upsert(record.upsert or request.upsert) if needs_per_record_upsert else None,
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
        # index is each record's position in the original request.records list, so callers can
        # correlate a result back via request.records[result['index']].
        successes, errors = [], []
        for offset, record in enumerate(records):
            index = start_index + offset
            if record.error is not None:
                errors.append({'index': index, 'error': record.error, 'code': record.http_code, 'request_id': request_id})
            else:
                successes.append({
                    'index': index,
                    'skyflow_id': record.skyflow_id,
                    'tokens': self.__to_token_map(record.tokens),
                    'data': record.data,
                    'table': record.table_name,
                })
        return successes, errors

    def __to_token_map(self, tokens):
        if not tokens:
            return None
        token_map = {}
        for column, entries in tokens.items():
            if isinstance(entries, list):
                token_map[column] = [
                    {'token': entry.get('token'), 'token_group_name': entry.get('tokenGroupName')}
                    for entry in entries if isinstance(entry, dict)
                ]
            else:
                token_map[column] = entries
        return token_map

    def __errors_from_exception(self, e, batch_records, start_index):
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
                    return [self.__error_dict_from_record_map(err_field, start_index + i, request_id) for i in range(len(batch_records))]
                return [{'index': start_index + i, 'error': str(err_field), 'code': e.status_code, 'request_id': request_id}
                        for i in range(len(batch_records))]
            return [{'index': start_index + i, 'error': str(e), 'code': e.status_code, 'request_id': request_id}
                    for i in range(len(batch_records))]
        message = str(e) if e else CommonMessages.Error.GENERIC_API_ERROR.value
        return [{'index': start_index + i, 'error': message, 'code': None, 'request_id': None} for i in range(len(batch_records))]

    def __error_dict_from_record_map(self, record_map, index, request_id):
        code = record_map.get('http_code', record_map.get('httpCode', record_map.get('statusCode')))
        message = record_map.get('error', record_map.get('message', 'Unknown error'))
        return {'index': index, 'error': message, 'code': code, 'request_id': request_id}
