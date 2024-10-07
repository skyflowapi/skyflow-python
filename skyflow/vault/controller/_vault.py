from samples.v2sample import response
from skyflow.generated.rest import V1FieldRecords, RecordServiceInsertRecordBody, V1DetokenizeRecordRequest, \
    V1DetokenizePayload, V1TokenizeRecordRequest, V1TokenizePayload, QueryServiceExecuteQueryBody, \
    RecordServiceBulkDeleteRecordBody, RecordServiceUpdateRecordBody
from skyflow.utils import get_redaction_type
from skyflow.utils.validations import validate_insert_request
from skyflow.vault.data import InsertRequest, UpdateRequest, DeleteRequest, GetRequest, UploadFileRequest, QueryRequest, \
    InsertResponse, GetResponse, QueryResponse
from skyflow.vault.tokens import DetokenizeRequest, TokenizeRequest, DetokenizeResponse, TokenizeResponse
from skyflow.error import SkyflowError

class Vault:
    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def insert(self, request: InsertRequest):
        validate_insert_request(request)
        self.__vault_client.initialize_client_configuration()
        records_api = self.__vault_client.get_records_api()
        records_list = []
        for record in request.values:
            records_list.append(
                V1FieldRecords(
                    fields = record
                )
            )
        body = RecordServiceInsertRecordBody(
            records = records_list,
            tokenization = request.return_tokens,
            upsert=request.upsert,
            homogeneous=request.homogeneous,
        )
        try:
            api_response = records_api.record_service_insert_record(self.__vault_client.get_vault_id(), request.table_name, body)
            response = InsertResponse.parse_insert_response(api_response)
            return response
        except Exception:
            raise SkyflowError("Insert Failed")

    def update(self, request: UpdateRequest):
        self.__vault_client.initialize_client_configuration()
        records_api = self.__vault_client.get_records_api()
        table_name = request.table

        fields = {key: value for key, value in request.data.items() if key != "id"}
        record = V1FieldRecords(fields=fields)
        payload = RecordServiceUpdateRecordBody(record=record, tokenization=True)
        try:
            response = records_api.record_service_update_record(self.__vault_client.get_vault_id(), table_name, request.data.id, payload)
            return response
        except Exception:
            raise SkyflowError("Update Failed")

    def delete(self, request: DeleteRequest):
        # validate_delete_request(request)
        self.__vault_client.initialize_client_configuration()
        records_api = self.__vault_client.get_records_api()
        table_name = request.table
        skyflow_ids = request.ids
        payload = RecordServiceBulkDeleteRecordBody(
            skyflow_ids = skyflow_ids
        )
        try:
            response = records_api.record_service_bulk_delete_record(self.__vault_client.get_vault_id(), table_name, payload)
            return response
        except Exception:
            raise SkyflowError("Bulk Delete Failed")



    def get(self, request: GetRequest):
        # validate_get_request(request)
        self.__vault_client.initialize_client_configuration()
        records_api = self.__vault_client.get_records_api()
        skyflow_ids = request.ids
        try:
            api_response = records_api.record_service_bulk_get_record(self.__vault_client.get_vault_id(),
                                                                  table_name = request.table,
                                                                  skyflow_ids=skyflow_ids,
                                                                  redaction=get_redaction_type(request.redaction_type),
                                                                  tokenization=request.tokenization,
                                                                  fields=request.fields,
                                                                  offset=request.offset,
                                                                  limit=request.limit,
                                                                  download_url=request.download_url,
                                                                  column_name=request.column_name,
                                                                  column_values=request.column_values,
                                                                  order_by=request.order_by)

            response = GetResponse.parsed_get_response(api_response)
            return response

        except Exception:
            raise SkyflowError("Get Failed")

    def query(self, request: QueryRequest):
        self.__vault_client.initialize_client_configuration()
        query_api = self.__vault_client.get_query_api()
        payload = QueryServiceExecuteQueryBody(query = request.query)

        try:
            api_response = query_api.query_service_execute_query(self.__vault_client.get_vault_id(), payload)
            response = QueryResponse.parse_query_response(api_response)
            return response
        except Exception:
            raise SkyflowError("Query Failed")


    def detokenize(self, request: DetokenizeRequest):
        # validate_detokenize_request(request)
        self.__vault_client.initialize_client_configuration()
        tokens_api = self.__vault_client.get_tokens_api()
        tokens_list = []
        for token in request.tokens:
                tokens_list.append(
                    V1DetokenizeRecordRequest(token=token, redaction=get_redaction_type(request.redaction_type)),
                )

        payload = V1DetokenizePayload(detokenization_parameters=tokens_list, continue_on_error=request.continue_on_error)
        try:
            api_response = tokens_api.record_service_detokenize(self.__vault_client.get_vault_id(), detokenize_payload=payload)
            response = DetokenizeResponse.parse_detokenize_response(api_response)
            return response
        except Exception:
            SkyflowError("Detokenize Failed")

    def tokenize(self, request: TokenizeRequest):
        self.__vault_client.initialize_client_configuration()
        tokens_api = self.__vault_client.get_tokens_api()
        records_list = []

        for value in request.values:
            records_list.append(
                V1TokenizeRecordRequest(value=value, column_group=request.column_group),
            )
        payload = V1TokenizePayload(tokenization_parameters=records_list)
        try:
            api_response = tokens_api.record_service_tokenize(self.__vault_client.get_vault_id(), tokenize_payload=payload)
            response = TokenizeResponse.parse_tokenize_response(api_response)
            return response
        except Exception as e:
            SkyflowError("Tokenize Failed")
