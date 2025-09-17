import base64
import json
import os
from typing import Optional
from skyflow.generated.rest import V1FieldRecords, V1BatchRecord, V1TokenizeRecordRequest, \
    V1DetokenizeRecordRequest
from skyflow.generated.rest.core.file import File
from skyflow.utils import SkyflowMessages, parse_insert_response, \
    handle_exception, parse_update_record_response, parse_delete_response, parse_detokenize_response, \
    parse_tokenize_response, parse_query_response, parse_get_response, encode_column_values, get_metrics
from skyflow.utils.constants import SKY_META_DATA_HEADER
from skyflow.utils.enums import RequestMethod
from skyflow.utils.enums.redaction_type import RedactionType
from skyflow.utils.logger import log_info, log_error_log
from skyflow.utils.validations import validate_insert_request, validate_delete_request, validate_query_request, \
    validate_get_request, validate_update_request, validate_detokenize_request, validate_tokenize_request, validate_file_upload_request
from skyflow.vault.data import InsertRequest, UpdateRequest, DeleteRequest, GetRequest, QueryRequest, FileUploadRequest, FileUploadResponse
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
                bulk_record_list.append(bulk_record)
            return bulk_record_list

    def __build_batch_field_records(self, values, tokens, table_name, return_tokens, upsert):
        batch_record_list = []
        for i, value in enumerate(values):
            token = tokens[i] if tokens is not None and i < len(tokens) else None
            batch_record = V1BatchRecord(
                fields=value,
                table_name=table_name,
                method=RequestMethod.POST.value,
                tokenization=return_tokens,
                upsert=upsert,
                tokens=token
            )
            batch_record_list.append(batch_record)
        return batch_record_list

    def __build_insert_body(self, request: InsertRequest):
        if request.continue_on_error:
            records_list = self.__build_batch_field_records(
                request.values,
                request.tokens,
                request.table,
                request.return_tokens,
                request.upsert
            )

            return records_list
        else:
            records_list = self.__build_bulk_field_records(request.values, request.tokens)
            return records_list
        
    def __get_file_for_file_upload(self, request: FileUploadRequest) -> Optional[File]:
        if request.file_path:
            if not request.file_name:
                request.file_name = os.path.basename(request.file_path)

            with open(request.file_path, "rb") as f:
                file_bytes = f.read()
            return (request.file_name, file_bytes)

        elif request.base64 and request.file_name:
            decoded_bytes = base64.b64decode(request.base64)
            return (request.file_name, decoded_bytes)

        elif request.file_object is not None:
            if hasattr(request.file_object, "name") and request.file_object.name:
                file_name = os.path.basename(request.file_object.name)
                return (file_name, request.file_object)

        return None
    
    def __get_headers(self):
        headers = {
            SKY_META_DATA_HEADER: json.dumps(get_metrics())
        }
        return headers

    def insert(self, request: InsertRequest):
        log_info(SkyflowMessages.Info.VALIDATE_INSERT_REQUEST.value, self.__vault_client.get_logger())
        validate_insert_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.INSERT_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        records_api = self.__vault_client.get_records_api().with_raw_response
        insert_body = self.__build_insert_body(request)

        try:
            log_info(SkyflowMessages.Info.INSERT_TRIGGERED.value, self.__vault_client.get_logger())
            if request.continue_on_error:
                api_response = records_api.record_service_batch_operation(self.__vault_client.get_vault_id(),
                                                                          records=insert_body, continue_on_error=request.continue_on_error, byot=request.token_mode.value, request_options=self.__get_headers())

            else:
                api_response = records_api.record_service_insert_record(self.__vault_client.get_vault_id(),
                                                                        request.table, records=insert_body,tokenization= request.return_tokens, upsert=request.upsert, homogeneous=request.homogeneous, byot=request.token_mode.value, request_options=self.__get_headers())

            insert_response = parse_insert_response(api_response, request.continue_on_error)
            log_info(SkyflowMessages.Info.INSERT_SUCCESS.value, self.__vault_client.get_logger())
            return insert_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.INSERT_RECORDS_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def update(self, request: UpdateRequest):
        log_info(SkyflowMessages.Info.VALIDATE_UPDATE_REQUEST.value, self.__vault_client.get_logger())
        validate_update_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.UPDATE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        field = {key: value for key, value in request.data.items() if key != "skyflow_id"}
        record = V1FieldRecords(fields=field, tokens = request.tokens)

        records_api = self.__vault_client.get_records_api()
        try:
            log_info(SkyflowMessages.Info.UPDATE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = records_api.record_service_update_record(
                self.__vault_client.get_vault_id(),
                request.table,
                id=request.data.get("skyflow_id"),
                record=record,
                tokenization=request.return_tokens,
                byot=request.token_mode.value,
                request_options = self.__get_headers()
            )
            log_info(SkyflowMessages.Info.UPDATE_SUCCESS.value, self.__vault_client.get_logger())
            update_response = parse_update_record_response(api_response)
            return update_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.UPDATE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def delete(self, request: DeleteRequest):
        log_info(SkyflowMessages.Info.VALIDATING_DELETE_REQUEST.value, self.__vault_client.get_logger())
        validate_delete_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DELETE_REQUEST_RESOLVED.value,  self.__vault_client.get_logger())
        self.__initialize()
        records_api = self.__vault_client.get_records_api()
        try:
            log_info(SkyflowMessages.Info.DELETE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = records_api.record_service_bulk_delete_record(
                self.__vault_client.get_vault_id(),
                request.table,
                skyflow_ids=request.ids,
                request_options=self.__get_headers()
            )
            log_info(SkyflowMessages.Info.DELETE_SUCCESS.value, self.__vault_client.get_logger())
            delete_response = parse_delete_response(api_response)
            return delete_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DELETE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def get(self, request: GetRequest):
        log_info(SkyflowMessages.Info.VALIDATE_GET_REQUEST.value, self.__vault_client.get_logger())
        validate_get_request(self.__vault_client.get_logger(), request)
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
                request_options=self.__get_headers()
            )
            log_info(SkyflowMessages.Info.GET_SUCCESS.value, self.__vault_client.get_logger())
            get_response = parse_get_response(api_response)
            return get_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def query(self, request: QueryRequest):
        log_info(SkyflowMessages.Info.VALIDATING_QUERY_REQUEST.value, self.__vault_client.get_logger())
        validate_query_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.QUERY_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        query_api = self.__vault_client.get_query_api()
        try:
            log_info(SkyflowMessages.Info.QUERY_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = query_api.query_service_execute_query(
                self.__vault_client.get_vault_id(),
                query=request.query,
                request_options=self.__get_headers()
            )
            log_info(SkyflowMessages.Info.QUERY_SUCCESS.value, self.__vault_client.get_logger())
            query_response = parse_query_response(api_response)
            return query_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.QUERY_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def detokenize(self, request: DetokenizeRequest):
        log_info(SkyflowMessages.Info.VALIDATE_DETOKENIZE_REQUEST.value, self.__vault_client.get_logger())
        validate_detokenize_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DETOKENIZE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        tokens_list = [
            V1DetokenizeRecordRequest(
                token=item.get('token'),
                redaction=item.get('redaction', RedactionType.DEFAULT)
            )
            for item in request.data
        ]
        tokens_api = self.__vault_client.get_tokens_api().with_raw_response
        try:
            log_info(SkyflowMessages.Info.DETOKENIZE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = tokens_api.record_service_detokenize(
                self.__vault_client.get_vault_id(),
                detokenization_parameters=tokens_list,
                continue_on_error = request.continue_on_error,
                request_options=self.__get_headers()
            )
            log_info(SkyflowMessages.Info.DETOKENIZE_SUCCESS.value, self.__vault_client.get_logger())
            detokenize_response = parse_detokenize_response(api_response)
            return detokenize_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETOKENIZE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
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
        tokens_api = self.__vault_client.get_tokens_api()
        try:
            log_info(SkyflowMessages.Info.TOKENIZE_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = tokens_api.record_service_tokenize(
                self.__vault_client.get_vault_id(),
                tokenization_parameters=records_list,
                request_options=self.__get_headers()
            )
            tokenize_response = parse_tokenize_response(api_response)
            log_info(SkyflowMessages.Info.TOKENIZE_SUCCESS.value, self.__vault_client.get_logger())
            return tokenize_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.TOKENIZE_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def upload_file(self, request: FileUploadRequest):
        log_info(SkyflowMessages.Info.FILE_UPLOAD_TRIGGERED.value, self.__vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATING_FILE_UPLOAD_REQUEST.value, self.__vault_client.get_logger())
        validate_file_upload_request(self.__vault_client.get_logger(), request)
        self.__initialize()
        file_upload_api = self.__vault_client.get_records_api().with_raw_response
        try:
            api_response = file_upload_api.upload_file_v_2(
                self.__vault_client.get_vault_id(),
                table_name=request.table,
                column_name=request.column_name,
                file=self.__get_file_for_file_upload(request),
                skyflow_id=request.skyflow_id,
                return_file_metadata= False,
                request_options=self.__get_headers()
            )
            log_info(SkyflowMessages.Info.FILE_UPLOAD_REQUEST_RESOLVED.value, self.__vault_client.get_logger())            
            log_info(SkyflowMessages.Info.FILE_UPLOAD_SUCCESS.value, self.__vault_client.get_logger())
            upload_response = FileUploadResponse(
                skyflow_id=api_response.data.skyflow_id,
                errors=None
            )
            return upload_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.FILE_UPLOAD_REQUEST_REJECTED.value, logger = self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
