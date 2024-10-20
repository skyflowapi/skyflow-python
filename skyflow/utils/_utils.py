import os
import json
from urllib.parse import urlparse
import urllib.parse
import requests
import platform
import sys
from requests import PreparedRequest
from skyflow.error import SkyflowError
from skyflow.generated.rest import RedactionEnumREDACTION, V1UpdateRecordResponse, V1BulkDeleteRecordResponse, \
    V1DetokenizeResponse, V1TokenizeResponse, V1GetQueryResponse, V1BulkGetRecordResponse
from . import SkyflowMessages, SDK_VERSION, log_error
from .enums import Env, ContentType, Redaction
import skyflow.generated.rest as vault_client
from skyflow.vault.data import InsertResponse, UpdateResponse, DeleteResponse, QueryResponse, GetResponse
from .validations import validate_invoke_connection_params
from ..vault.tokens import DetokenizeResponse, TokenizeResponse

invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value

def get_credentials(config_level_creds = None, common_skyflow_creds = None):
    env_skyflow_credentials = os.getenv("SKYFLOW_CREDENTIALS")
    if config_level_creds:
        return config_level_creds
    if common_skyflow_creds:
        return common_skyflow_creds
    if env_skyflow_credentials:
        return env_skyflow_credentials
    else:
        raise Exception("Invalid Credentials")
    pass


def get_vault_url(cluster_id, env):
    if env == Env.PROD:
        return f"http://{cluster_id}.vault.skyflowapis.com"
    elif env == Env.SANDBOX:
        return f"https://{cluster_id}.vault.skyflowapis-preview.com"
    elif env == Env.DEV:
        return f"https://{cluster_id}.vault.skyflowapis.dev"
    else:
        return f"https://{cluster_id}.vault.skyflowapis.com"

def get_client_configuration(vault_url, bearer_token):
        return vault_client.Configuration(
            host=vault_url,
            api_key_prefix="Bearer",
            api_key=bearer_token
        )

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def format_scope(scopes):
    if not scopes:
        return None
    return " ".join([f"role:{scope}" for scope in scopes])


def parse_path_params(url, path_params):
    result = url
    for param, value in path_params.items():
        result = result.replace('{' + param + '}', value)

    return result

def to_lowercase_keys(dict):
    '''
        convert keys of dictionary to lowercase
    '''
    result = {}
    for key, value in dict.items():
        result[key.lower()] = value

    return result

def construct_invoke_connection_request(request, connection_url, logger) -> PreparedRequest:
    url = parse_path_params(connection_url.rstrip('/'), request.path_params)

    try:
        if isinstance(request.request_headers, dict):
            header = to_lowercase_keys(json.loads(
                json.dumps(request.request_headers)))
        else:
            raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_BODY.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    except Exception:
        raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    if not 'Content-Type'.lower() in header:
        header['content-type'] = ContentType.JSON

    try:
        if isinstance(request.body, dict):
            json_data, files = get_data_from_content_type(
                request.body, header["content-type"]
            )
        else:
            raise SkyflowError(SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value, invalid_input_error_code, logger = logger, logger_method=log_error)
    except Exception as e:
        raise SkyflowError( SkyflowMessages.Error.INVALID_REQUEST_HEADERS.value, invalid_input_error_code, logger = logger, logger_method=log_error)

    validate_invoke_connection_params(logger, request.query_params, request.path_params)

    try:
        return requests.Request(
            method = request.method,
            url = url,
            data = json_data,
            headers = header,
            params = request.params,
            files = files
        ).prepare()
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowMessages.Error.INVALID_URL.value.format(connection_url), invalid_input_error_code, logger = logger, logger_method=log_error)


def http_build_query(data):
    '''
        Creates a form urlencoded string from python dictionary
        urllib.urlencode() doesn't encode it in a php-esque way, this function helps in that
    '''

    return urllib.parse.urlencode(r_urlencode(list(), dict(), data))

def r_urlencode(parents, pairs, data):
    '''
        convert the python dict recursively into a php style associative dictionary
    '''
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
    '''
        renders the nested dictionary key as an associative array (php style dict)
    '''
    depth, out_str = 0, ''
    for x in parents:
        s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
        out_str += s % str(x)
        depth += 1
    return out_str

def get_data_from_content_type(data, content_type):
    '''
        Get request data according to content type
    '''
    converted_data = data
    files = {}
    if content_type == ContentType.URLENCODED:
        converted_data = http_build_query(data)
    elif content_type == ContentType.FORMDATA:
        converted_data = r_urlencode(list(), dict(), data)
        files = {(None, None)}
    elif content_type == ContentType.JSON:
        converted_data = json.dumps(data)

    return converted_data, files


def get_metrics():
    ''' fetch metrics
    '''
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
    inserted_fields = []
    errors = []
    insert_response = InsertResponse()
    if continue_on_error:
        for idx, response in enumerate(api_response.responses):
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
                    'error': response['Body']['error']
                }
                errors.append(error)

            insert_response.inserted_fields = inserted_fields
            insert_response.error_data = errors

    else:
        for record in api_response.records:
            field_data = {
                'skyflow_id': record.skyflow_id
            }

            if record.tokens:
                field_data.update(record.tokens)

            inserted_fields.append(field_data)
        insert_response.inserted_fields = inserted_fields

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
    delete_response.error = []
    return delete_response


def parse_get_response(api_response: V1BulkGetRecordResponse):
    get_response = GetResponse()
    data = []
    error = []
    for record in api_response.records:
        field_data = {field: value for field, value in record.fields.items()}
        data.append(field_data)

    get_response.data = data
    get_response.error = error

    return get_response

def parse_detokenize_response(api_response: V1DetokenizeResponse):
    detokenized_fields = []
    errors = []

    for record in api_response.records:
        if record.error:
            errors.append({
                "token": record.token,
                "error": record.error
            })
        else:
            value_type = record.value_type.value if record.value_type else None
            detokenized_fields.append({
                "token": record.token,
                "value": record.value,
                "type": value_type
            })

    detokenized_fields = detokenized_fields
    errors = errors
    detokenize_response = DetokenizeResponse()
    detokenize_response.detokenized_fields = detokenized_fields
    detokenize_response.errors = errors

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


def log_and_reject_error(description, status_code, request_id, http_status=None, grpc_code=None, details=None, logger = None):
    log_error(description, status_code, request_id, grpc_code, http_status, details, logger= logger)

def handle_exception(error, logger):
    request_id = error.headers.get('x-request-id', 'unknown-request-id')
    content_type = error.headers.get('content-type')
    data = error.body

    # Call relevant handler based on content type
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
        description = json.loads(data)
        status_code = description.get('error', {}).get('http_code', 500)  # Default to 500 if not found
        http_status = description.get('error', {}).get('http_status')
        grpc_code = description.get('error', {}).get('grpc_code')
        details = description.get('error', {}).get('details')

        description_message = description.get('error', {}).get('message', "An unknown error occurred.")
        log_and_reject_error(description_message, status_code, request_id, http_status, grpc_code, details, logger = logger)
    except json.JSONDecodeError:
        log_and_reject_error("Invalid JSON response received.", err, request_id, logger = logger)

def handle_text_error(err, data, request_id, logger):
    log_and_reject_error(data, err, request_id, logger =  logger)

def handle_generic_error(err, request_id, logger):
    description = "An error occurred."
    log_and_reject_error(description, err, request_id, logger = logger)
