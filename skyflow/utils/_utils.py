import os
import json
import urllib.parse
from dotenv import load_dotenv
import dotenv
import httpx
from requests.sessions import PreparedRequest
from requests.models import HTTPError
import requests
import platform
import sys
import re
from urllib.parse import quote
from skyflow.error import SkyflowError
from skyflow.generated.rest import V1UpdateRecordResponse, V1BulkDeleteRecordResponse, \
    V1DetokenizeResponse, V1TokenizeResponse, V1GetQueryResponse, V1BulkGetRecordResponse, \
    DeidentifyStringResponse, ErrorResponse, IdentifyResponse
from skyflow.generated.rest.core.http_response import HttpResponse
from skyflow.utils.logger import log_error_log
from skyflow.vault.detect import DeidentifyTextResponse, ReidentifyTextResponse
from skyflow.vault.detect import EntityInfo, TextIndex
from . import SkyflowMessages, SDK_VERSION
from .constants import PROTOCOL
from .enums import Env, ContentType, EnvUrls
from skyflow.vault.data import InsertResponse, UpdateResponse, DeleteResponse, QueryResponse, GetResponse
from .validations import validate_invoke_connection_params
from ..vault.connection import InvokeConnectionResponse
from ..vault.tokens import DetokenizeResponse, TokenizeResponse

invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def get_credentials(config_level_creds = None, common_skyflow_creds = None, logger = None):
    dotenv.load_dotenv()
    dotenv_path = dotenv.find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)
    env_skyflow_credentials = os.getenv("SKYFLOW_CREDENTIALS")
    if config_level_creds:
        return config_level_creds
    if common_skyflow_creds:
        return common_skyflow_creds
    if env_skyflow_credentials:
        env_skyflow_credentials.strip()
        try:
            env_creds = env_skyflow_credentials.replace('\n', '\\n')
            return {
                'credentials_string': env_creds
            }
        except json.JSONDecodeError:
            raise SkyflowError(SkyflowMessages.Error.INVALID_JSON_FORMAT_IN_CREDENTIALS_ENV.value, invalid_input_error_code)
    else:
        raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS.value, invalid_input_error_code)

def validate_api_key(api_key: str, logger = None) -> bool:
    if len(api_key) != 42:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_API_KEY.value, logger = logger)
        return False
    api_key_pattern = re.compile(r'^sky-[a-zA-Z0-9]{5}-[a-fA-F0-9]{32}$')

    return bool(api_key_pattern.match(api_key))

def get_vault_url(cluster_id, env,vault_id, logger = None):
    if not cluster_id or not isinstance(cluster_id, str) or not cluster_id.strip():
        raise SkyflowError(SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id), invalid_input_error_code)

    if env not in Env:
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    base_url = EnvUrls[env.name].value
    protocol = PROTOCOL

    return f"{protocol}://{cluster_id}.{base_url}"

def parse_path_params(url, path_params):
    result = url
    for param, value in path_params.items():
        result = result.replace('{' + param + '}', value)

    return result

def to_lowercase_keys(dict):
    result = {}
    for key, value in dict.items():
        result[key.lower()] = value

    return result

def convert_detected_entity_to_entity_info(detected_entity):
    return EntityInfo(
        token=detected_entity.token,
        value=detected_entity.value,
        text_index=TextIndex(
            start=detected_entity.location.start_index,
            end=detected_entity.location.end_index
        ),
        processed_index=TextIndex(
            start=detected_entity.location.start_index_processed,
            end=detected_entity.location.end_index_processed
        ),
        entity=detected_entity.entity_type,
        scores=detected_entity.entity_scores
    )

def construct_invoke_connection_request(request, connection_url, logger) -> PreparedRequest:
    url = parse_path_params(connection_url.rstrip('/'), request.path_params)

    try:
        if isinstance(request.headers, dict):
            header = to_lowercase_keys(json.loads(
                json.dumps(request.headers)))
        else:
            raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value, invalid_input_error_code)
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value, invalid_input_error_code)

    if not 'Content-Type'.lower() in header:
        header['content-type'] = ContentType.JSON.value

    try:
        if isinstance(request.body, dict):
            json_data, files = get_data_from_content_type(
                request.body, header["content-type"]
            )
        else:
            raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_BODY.value, invalid_input_error_code)
    except Exception as e:
        raise SkyflowError( SkyflowMessages.Error.INVALID_REQUEST_BODY.value, invalid_input_error_code)

    validate_invoke_connection_params(logger, request.query_params, request.path_params)

    if not hasattr(request.method, 'value'):
        raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_METHOD.value, invalid_input_error_code)

    try:
        return requests.Request(
            method = request.method.value,
            url = url,
            data = json_data,
            headers = header,
            params = request.query_params,
            files = files
        ).prepare()
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_URL.value.format(connection_url), invalid_input_error_code)


def http_build_query(data):
    return urllib.parse.urlencode(r_urlencode(list(), dict(), data))

def r_urlencode(parents, pairs, data):
    if isinstance(data, list) or isinstance(data, tuple):
        for i in range(len(data)):
            parents.append(i)
            r_urlencode(parents, pairs, data[i])
            parents.pop()
    elif isinstance(data, dict):
        for key, value in data.items():
            parents.append(key)
            r_urlencode(parents, pairs, value)
            parents.pop()
    else:
        pairs[render_key(parents)] = str(data)

    return pairs

def render_key(parents):
    depth, out_str = 0, ''
    for x in parents:
        s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
        out_str += s % str(x)
        depth += 1
    return out_str

def get_data_from_content_type(data, content_type):
    converted_data = data
    files = {}
    if content_type == ContentType.URLENCODED.value:
        converted_data = http_build_query(data)
    elif content_type == ContentType.FORMDATA.value:
        converted_data = r_urlencode(list(), dict(), data)
        files = {(None, None)}
    elif content_type == ContentType.JSON.value:
        converted_data = json.dumps(data)

    return converted_data, files


def get_metrics():
    sdk_name_version = "skyflow-python@" + SDK_VERSION

    try:
        sdk_client_device_model = platform.node()
    except Exception:
        sdk_client_device_model = ""

    try:
        sdk_client_os_details = sys.platform
    except Exception:
        sdk_client_os_details = ""

    try:
        sdk_runtime_details = sys.version
    except Exception:
        sdk_runtime_details = ""

    details_dic = {
        'sdk_name_version': sdk_name_version,
        'sdk_client_device_model': sdk_client_device_model,
        'sdk_client_os_details': sdk_client_os_details,
        'sdk_runtime_details': "Python " + sdk_runtime_details,
    }
    return details_dic

def parse_insert_response(api_response, continue_on_error):
    # Retrieve the headers and data from the API response
    api_response_headers = api_response.headers
    api_response_data = api_response.data
    # Retrieve the request ID from the headers
    request_id = api_response_headers.get('x-request-id')
    inserted_fields = []
    errors = []
    insert_response = InsertResponse()
    if continue_on_error:
        for idx, response in enumerate(api_response_data.responses):
            if response['Status'] == 200:
                body = response['Body']
                if 'records' in body:
                    for record in body['records']:
                        inserted_field = {
                            'skyflow_id': record['skyflow_id'],
                            'request_index': idx
                        }

                        if 'tokens' in record:
                            inserted_field.update(record['tokens'])
                        inserted_fields.append(inserted_field)
            elif response['Status'] == 400:
                error = {
                    'request_index': idx,
                    'request_id': request_id,
                    'error': response['Body']['error'],
                    'http_code': response['Status'],
                }
                errors.append(error)

            insert_response.inserted_fields = inserted_fields
            insert_response.errors = errors if len(errors) > 0 else None
    else:
        for record in api_response_data.records:
            field_data = {
                'skyflow_id': record.skyflow_id
            }

            if record.tokens:
                field_data.update(record.tokens)

            inserted_fields.append(field_data)
        insert_response.inserted_fields = inserted_fields
        insert_response.errors = None

    return insert_response

def parse_update_record_response(api_response: V1UpdateRecordResponse):
    update_response = UpdateResponse()
    updated_field = dict()
    updated_field['skyflow_id'] = api_response.skyflow_id
    if api_response.tokens is not None:
        updated_field.update(api_response.tokens)

    update_response.updated_field = updated_field

    return update_response

def parse_delete_response(api_response: V1BulkDeleteRecordResponse):
    delete_response = DeleteResponse()
    deleted_ids = api_response.record_id_response
    delete_response.deleted_ids = deleted_ids
    delete_response.errors = None
    return delete_response

def parse_get_response(api_response: V1BulkGetRecordResponse):
    get_response = GetResponse()
    data = []
    for record in api_response.records:
        field_data = {field: value for field, value in record.fields.items()}
        data.append(field_data)

    get_response.data = data
    return get_response

def parse_detokenize_response(api_response: HttpResponse[V1DetokenizeResponse]):
    # Retrieve the headers and data from the API response
    api_response_headers = api_response.headers
    api_response_data = api_response.data
    # Retrieve the request ID from the headers
    request_id = api_response_headers.get('x-request-id')
    detokenized_fields = []
    errors = []

    for record in api_response_data.records:
        if record.error:
            errors.append({
                "token": record.token,
                "error": record.error,
                "request_id": request_id
            })
        else:
            value_type = record.value_type if record.value_type else None
            detokenized_fields.append({
                "token": record.token,
                "value": record.value,
                "type": value_type
            })

    detokenized_fields = detokenized_fields
    errors = errors
    detokenize_response = DetokenizeResponse()
    detokenize_response.detokenized_fields = detokenized_fields
    detokenize_response.errors = errors if len(errors) > 0 else None

    return detokenize_response

def parse_tokenize_response(api_response: V1TokenizeResponse):
    tokenize_response = TokenizeResponse()
    tokenized_fields = [{"token": record.token} for record in api_response.records]

    tokenize_response.tokenized_fields = tokenized_fields

    return tokenize_response

def parse_query_response(api_response: V1GetQueryResponse):
    query_response = QueryResponse()
    fields = []
    for record in api_response.records:
        field_object = {
            **record.fields,
            "tokenized_data": {}
        }
        fields.append(field_object)
    query_response.fields = fields
    return query_response

def parse_invoke_connection_response(api_response: requests.Response):
    status_code = api_response.status_code
    content = api_response.content
    if isinstance(content, bytes):
        content = content.decode('utf-8')
    try:
        api_response.raise_for_status()
        try:
            data = json.loads(content)
            metadata = {}
            if 'x-request-id' in api_response.headers:
                metadata['request_id'] = api_response.headers['x-request-id']

            return InvokeConnectionResponse(data=data, metadata=metadata, errors=None)
        except Exception as e:
            raise SkyflowError(SkyflowMessages.Error.RESPONSE_NOT_JSON.value.format(content), status_code)
    except HTTPError:
        message = SkyflowMessages.Error.API_ERROR.value.format(status_code)  
        try:
            error_response = json.loads(content)                    
            request_id = api_response.headers['x-request-id']
            error_from_client = api_response.headers.get('error-from-client')

            status_code = error_response.get('error', {}).get('http_code', 500)  # Default to 500 if not found
            http_status = error_response.get('error', {}).get('http_status')
            grpc_code = error_response.get('error', {}).get('grpc_code')
            details = error_response.get('error', {}).get('details')
            message = error_response.get('error', {}).get('message', "An unknown error occurred.")
            
            if error_from_client is not None:
                if details is None: details = []
                error_from_client_bool = error_from_client.lower() == 'true'
                details.append({'error_from_client': error_from_client_bool})

            raise SkyflowError(message, status_code, request_id, grpc_code, http_status, details)
        except json.JSONDecodeError:
            message = SkyflowMessages.Error.RESPONSE_NOT_JSON.value.format(content)
        raise SkyflowError(message, status_code)

def parse_deidentify_text_response(api_response: DeidentifyStringResponse):
    entities = [convert_detected_entity_to_entity_info(entity) for entity in api_response.entities]
    return DeidentifyTextResponse(
        processed_text=api_response.processed_text,
        entities=entities,
        word_count=api_response.word_count,
        char_count=api_response.character_count
    )

def parse_reidentify_text_response(api_response: IdentifyResponse):
    return ReidentifyTextResponse(api_response.text)

def log_and_reject_error(description, status_code, request_id, http_status=None, grpc_code=None, details=None, logger = None):
    raise SkyflowError(description, status_code, request_id, grpc_code, http_status, details)

def handle_exception(error, logger):
    # handle invalid cluster ID error scenario
    if (isinstance(error, httpx.ConnectError)):
        handle_generic_error(error, None, SkyflowMessages.ErrorCodes.INVALID_INPUT.value, logger)
        
    request_id = error.headers.get('x-request-id', 'unknown-request-id')
    content_type = error.headers.get('content-type')
    data = error.body

    if content_type:
        if 'application/json' in content_type:
            handle_json_error(error, data, request_id, logger)
        elif 'text/plain' in content_type:
            handle_text_error(error, data, request_id, logger)
        else:
            handle_generic_error(error, request_id, logger)
    else:
        handle_generic_error(error, request_id, logger)

def handle_json_error(err, data, request_id, logger):
    try:
        if isinstance(data, dict):  # If data is already a dict
            description = data
        elif isinstance(data, ErrorResponse):
            description = data.dict()
        else:
            description = json.loads(data)
        status_code = description.get('error', {}).get('http_code', 500)  # Default to 500 if not found
        http_status = description.get('error', {}).get('http_status')
        grpc_code = description.get('error', {}).get('grpc_code')
        details = description.get('error', {}).get('details', [])

        description_message = description.get('error', {}).get('message', "An unknown error occurred.")
        log_and_reject_error(description_message, status_code, request_id, http_status, grpc_code, details, logger = logger)
    except json.JSONDecodeError:
        log_and_reject_error("Invalid JSON response received.", err, request_id, logger = logger)

def handle_text_error(err, data, request_id, logger):
    log_and_reject_error(data, err.status, request_id, logger =  logger)

def handle_generic_error(err, request_id, logger):
    handle_generic_error(err, request_id, err.status, logger = logger)

def handle_generic_error(err, request_id, status, logger):
    description = SkyflowMessages.Error.GENERIC_API_ERROR.value
    log_and_reject_error(description, status, request_id, logger = logger)

def encode_column_values(get_request):
    encoded_column_values = list()
    for column in get_request.column_values:
        encoded_column_values.append(quote(column))

    return encoded_column_values

def get_attribute(obj, camel_case, snake_case):
    return getattr(obj, camel_case, None) or getattr(obj, snake_case, None)
