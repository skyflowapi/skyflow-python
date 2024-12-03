from skyflow.generated.rest import V1FieldRecords, RecordServiceInsertRecordBody, V1DetokenizeRecordRequest, \
    V1DetokenizePayload, V1TokenizeRecordRequest, V1TokenizePayload, QueryServiceExecuteQueryBody, \
    RecordServiceBulkDeleteRecordBody, RecordServiceUpdateRecordBody, RecordServiceBatchOperationBody, V1BatchRecord, \
    BatchRecordMethod
from skyflow.generated.rest.exceptions import BadRequestException, UnauthorizedException
from skyflow.utils import SkyflowMessages, parse_insert_response, \
    handle_exception, parse_update_record_response, parse_delete_response, parse_detokenize_response, \
    parse_tokenize_response, parse_query_response, parse_get_response, encode_column_values
from skyflow.utils.logger import log_info, log_error_log
from skyflow.utils.validations import validate_insert_request, validate_delete_request, validate_query_request, \
    validate_get_request, validate_update_request, validate_detokenize_request, validate_tokenize_request
from skyflow.vault.data import InsertRequest, UpdateRequest, DeleteRequest, GetRequest, QueryRequest
from skyflow.vault.tokens import DetokenizeRequest, TokenizeRequest

class Vault:
    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def __initialize(self):
        self.__vault_client.initialize_client_configuration()

    def __build_bulk_field_records(self, values, tokens=None):
        if tokens is None:
            return [V1FieldRecords(fields=record) for record in values]
        else:
            bulk_record_list = []
            for i, value in enumerate(values):
                token = tokens[i] if tokens is not None and i < len(tokens) else None
                bulk_record = V1FieldRecords(
                    fields=value,
                    tokens=token
                )
                if token is not None:
                    bulk_record.tokens = token
                bulk_record_list.append(bulk_record)
            return bulk_record_list

    def __build_batch_field_records(self, values, tokens, table_name, return_tokens, upsert):
        batch_record_list = []
        for i, value in enumerate(values):
            token = tokens[i] if tokens is not None and i < len(tokens) else None
            batch_record = V1BatchRecord(
                fields=value,
                table_name=table_name,
                method=BatchRecordMethod.POST,
                tokenization=return_tokens,
                upsert=upsert,
                tokens=token
            )
            if token is not None:
                batch_record.tokens = token
            batch_record_list.append(batch_record)
        return batch_record_list

    def __build_insert_body(self, request: InsertRequest):
        if request.continue_on_error:
            records_list = self.__build_batch_field_records(
                request.values,
                request.tokens,
                request.table_name,
                request.return_tokens,
                request.upsert
            )
            body = RecordServiceBatchOperationBody(
                records=records_list,
                continue_on_error=request.continue_on_error,
                byot=request.token_mode.value
            )
            return body
        else:
            records_list = self.__build_bulk_field_records(request.values, request.tokens)
            return RecordServiceInsertRecordBody(
                records=records_list,
                tokenization=request.return_tokens,
                upsert=request.upsert,
                homogeneous=request.homogeneous,
                byot=request.token_mode.value
            )

    def insert(self, request: InsertRequest):
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self.__vault_client.get_logger())
        validate_insert_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        records_api = self.__vault_client.get_records_api()
        insert_body = self.__build_insert_body(request)

        try:
            log_info(SkyflowMessages.Info.INSERT_TRIGGERED.value, self.__vault_client.get_logger())

            if request.continue_on_error:
                api_response = records_api.record_service_batch_operation(self.__vault_client.get_vault_id(),
                                                                          insert_body)

            else:
                api_response = records_api.record_service_insert_record(self.__vault_client.get_vault_id(),
                                                                        request.table_name, insert_body)

            insert_response = parse_insert_response(api_response, request.continue_on_error)
            log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self.__vault_client.get_logger())
            return insert_response

        except BadRequestException as e:
            log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            handle_exception(e, self.__vault_client.get_logger())

    def update(self, request: UpdateRequest):
        log_info(SkyflowMessages.Info.VALIDATE_UPDATE_REQUEST.value, self.__vault_client.get_logger())
        validate_update_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.UPDATE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        field = {key: value for key, value in request.data.items() if key != "skyflow_id"}
        record = V1FieldRecords(fields=field, tokens = request.tokens)
        payload = RecordServiceUpdateRecordBody(record=record, tokenization=request.return_tokens, byot=request.token_mode.value)

        records_api = self.__vault_client.get_records_api()
        try:
            log_info(SkyflowMessages.Info.UPDATE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = records_api.record_service_update_record(
                self.__vault_client.get_vault_id(),
                request.table,
                request.data.get("skyflow_id"),
                payload
            )
            log_info(SkyflowMessages.Info.UPDATE_SUCCESS.value, self.__vault_client.get_logger())
            update_response = parse_update_record_response(api_response)
            return update_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.UPDATE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            handle_exception(e, self.__vault_client.get_logger())

    def delete(self, request: DeleteRequest):
        log_info(SkyflowMessages.Info.VALIDATING_DELETE_REQUEST.value, self.__vault_client.get_logger())
        validate_delete_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DELETE_REQUEST_RESOLVED.value,  self.__vault_client.get_logger())
        self.__initialize()
        payload = RecordServiceBulkDeleteRecordBody(skyflow_ids=request.ids)
        records_api = self.__vault_client.get_records_api()
        try:
            log_info(SkyflowMessages.Info.DELETE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = records_api.record_service_bulk_delete_record(
                self.__vault_client.get_vault_id(),
                request.table,
                payload
            )
            log_info(SkyflowMessages.Info.DELETE_SUCCESS.value, self.__vault_client.get_logger())
            delete_response = parse_delete_response(api_response)
            return delete_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_REQUEST_REJECTED.value,
                          logger=self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def get(self, request: GetRequest):
        log_info(SkyflowMessages.Info.VALIDATE_GET_REQUEST.value, self.__vault_client.get_logger())
        validate_get_request(self.__vault_client.get_logger(), request)
        if request.column_values:
            request.column_values = encode_column_values(request)
        log_info(SkyflowMessages.Info.GET_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        records_api = self.__vault_client.get_records_api()
        try:
            log_info(SkyflowMessages.Info.GET_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = records_api.record_service_bulk_get_record(
                self.__vault_client.get_vault_id(),
                object_name=request.table,
                skyflow_ids=request.ids,
                redaction = request.redaction_type.value if request.redaction_type is not None else None,
                tokenization=request.return_tokens,
                fields=request.fields,
                offset=request.offset,
                limit=request.limit,
                download_url=request.download_url,
                column_name=request.column_name,
                column_values=request.column_values,
            )
            log_info(SkyflowMessages.Info.GET_SUCCESS.value, self.__vault_client.get_logger())
            get_response = parse_get_response(api_response)
            return get_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def query(self, request: QueryRequest):
        log_info(SkyflowMessages.Info.VALIDATING_QUERY_REQUEST.value, self.__vault_client.get_logger())
        validate_query_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.QUERY_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        payload = QueryServiceExecuteQueryBody(query=request.query)
        query_api = self.__vault_client.get_query_api()
        try:
            log_info(SkyflowMessages.Info.QUERY_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = query_api.query_service_execute_query(
                self.__vault_client.get_vault_id(),
                payload
            )
            log_info(SkyflowMessages.Info.QUERY_SUCCESS.value, self.__vault_client.get_logger())
            query_response = parse_query_response(api_response)
            return query_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.QUERY_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            log_error_log(SkyflowMessages.ErrorLogs.QUERY_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def detokenize(self, request: DetokenizeRequest):
        log_info(SkyflowMessages.Info.VALIDATE_DETOKENIZE_REQUEST.value, self.__vault_client.get_logger())
        validate_detokenize_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DETOKENIZE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        tokens_list = [
            V1DetokenizeRecordRequest(token=token, redaction=request.redaction_type.value)
            for token in request.tokens
        ]
        payload = V1DetokenizePayload(detokenization_parameters=tokens_list, continue_on_error=request.continue_on_error)
        tokens_api = self.__vault_client.get_tokens_api()
        try:
            log_info(SkyflowMessages.Info.DETOKENIZE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = tokens_api.record_service_detokenize(
                self.__vault_client.get_vault_id(),
                detokenize_payload=payload
            )
            log_info(SkyflowMessages.Info.DETOKENIZE_SUCCESS.value, self.__vault_client.get_logger())
            detokenize_response = parse_detokenize_response(api_response)
            return detokenize_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_REQUEST_REJECTED.value,
                          logger=self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def tokenize(self, request: TokenizeRequest):
        log_info(SkyflowMessages.Info.VALIDATING_TOKENIZE_REQUEST.value, self.__vault_client.get_logger())
        validate_tokenize_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.TOKENIZE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()

        records_list = [
            V1TokenizeRecordRequest(value=item["value"], column_group=item["column_group"])
            for item in request.values
        ]
        payload = V1TokenizePayload(tokenization_parameters=records_list)
        tokens_api = self.__vault_client.get_tokens_api()
        try:
            log_info(SkyflowMessages.Info.TOKENIZE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = tokens_api.record_service_tokenize(
                self.__vault_client.get_vault_id(),
                tokenize_payload=payload
            )
            tokenize_response = parse_tokenize_response(api_response)
            log_info(SkyflowMessages.Info.TOKENIZE_SUCCESS.value, self.__vault_client.get_logger())
            return tokenize_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.TOKENIZE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
        except UnauthorizedException as e:
            log_error_log(SkyflowMessages.ErrorLogs.TOKENIZE_REQUEST_REJECTED.value,
                          logger=self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
