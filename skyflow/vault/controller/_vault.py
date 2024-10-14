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

    def __initialize(self):
        self.__vault_client.initialize_client_configuration()

    def __build_field_records(self, values):
        return [V1FieldRecords(fields=record) for record in values]

    def insert(self, request: InsertRequest):
        print(self.__vault_client.get_log_level())
        validate_insert_request(request)
        self.__initialize()
        records_list = self.__build_field_records(request.values)
        body = RecordServiceInsertRecordBody(
            records = records_list,
            tokenization = request.return_tokens,
            upsert=request.upsert,
            homogeneous=request.homogeneous,
        )
        records_api = self.__vault_client.get_records_api()
        try:
            api_response = records_api.record_service_insert_record(self.__vault_client.get_vault_id(), request.table_name, body)
            return InsertResponse.parse_insert_response(api_response)
        except Exception:
            raise SkyflowError("Insert Failed")

    def update(self, request: UpdateRequest):
        self.__initialize()
        fields = {key: value for key, value in request.data.items() if key != "id"}
        record = V1FieldRecords(fields=fields)
        payload = RecordServiceUpdateRecordBody(record=record, tokenization=True)

        records_api = self.__vault_client.get_records_api()
        try:
            api_response = records_api.record_service_update_record(
                self.__vault_client.get_vault_id(),
                request.table,
                request.data.id,
                payload
            )
            return api_response
        except Exception:
            raise SkyflowError("Update Failed")


def delete(self, request: DeleteRequest):
        # validate_delete_request(request)
        self._initialize()

        payload = RecordServiceBulkDeleteRecordBody(skyflow_ids=request.ids)
        records_api = self.__vault_client.get_records_api()
        try:
            api_response = records_api.record_service_bulk_delete_record(
                self.__vault_client.get_vault_id(),
                request.table,
                payload
            )
            return api_response
        except Exception:
            raise SkyflowError("Bulk Delete Failed")

def get(self, request: GetRequest):
    # validate_get_request(request)
    self._initialize()

    records_api = self.__vault_client.get_records_api()
    try:
        api_response = records_api.record_service_bulk_get_record(
            self.__vault_client.get_vault_id(),
            table_name=request.table,
            skyflow_ids=request.ids,
            redaction=get_redaction_type(request.redaction_type),
            tokenization=request.tokenization,
            fields=request.fields,
            offset=request.offset,
            limit=request.limit,
            download_url=request.download_url,
            column_name=request.column_name,
            column_values=request.column_values,
            order_by=request.order_by
        )
        return GetResponse.parsed_get_response(api_response)
    except Exception:
        raise SkyflowError("Get Failed")

def query(self, request: QueryRequest):
    self._initialize()

    payload = QueryServiceExecuteQueryBody(query=request.query)
    query_api = self.__vault_client.get_query_api()
    try:
        api_response = query_api.query_service_execute_query(
            self.__vault_client.get_vault_id(),
            payload
        )
        return QueryResponse.parse_query_response(api_response)
    except Exception:
        raise SkyflowError("Query Failed")

def detokenize(self, request: DetokenizeRequest):
    # validate_detokenize_request(request)
    self._initialize()

    tokens_list = [
        V1DetokenizeRecordRequest(token=token, redaction=get_redaction_type(request.redaction_type))
        for token in request.tokens
    ]
    payload = V1DetokenizePayload(detokenization_parameters=tokens_list, continue_on_error=request.continue_on_error)
    tokens_api = self.__vault_client.get_tokens_api()
    try:
        api_response = tokens_api.record_service_detokenize(
            self.__vault_client.get_vault_id(),
            detokenize_payload=payload
        )
        return DetokenizeResponse.parse_detokenize_response(api_response)
    except Exception:
        raise SkyflowError("Detokenize Failed")

def tokenize(self, request: TokenizeRequest):
    self._initialize()

    records_list = [
        V1TokenizeRecordRequest(value=item["values"], column_group=item["cg"])
        for item in request.tokenize_parameters
    ]
    payload = V1TokenizePayload(tokenization_parameters=records_list)
    tokens_api = self.__vault_client.get_tokens_api()
    try:
        api_response = tokens_api.record_service_tokenize(
            self.__vault_client.get_vault_id(),
            tokenize_payload=payload
        )
        return TokenizeResponse.parse_tokenize_response(api_response)
    except Exception:
        raise SkyflowError("Tokenize Failed")
