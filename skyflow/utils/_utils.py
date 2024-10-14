import os
import json
from urllib.parse import urlparse
import urllib.parse
import requests
from skyflow.error import SkyflowError
from skyflow.generated.rest import RedactionEnumREDACTION, V1FieldRecords
from skyflow.utils.enums import Env, ContentType
import skyflow.generated.rest as vault_client

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


def get_redaction_type(redaction_type):
    if redaction_type == "plain-text":
        return RedactionEnumREDACTION.PLAIN_TEXT

def parse_path_params(url, path_params):
    result = url
    for param, value in path_params.items():
        result = result.replace('{' + param + '}', value)

    return result

def construct_invoke_connection_request(request, connection_url):
    url = parse_path_params(connection_url.rstrip('/'), connection_url.pathParams)
    header = dict()
    header['content-type'] = ContentType.JSON

    try:
        if isinstance(request.body, dict):
            json_data, files = get_data_from_content_type(
                request.body, header["content-type"]
            )
        else:
            raise SyntaxError("Given response body is not valid")
    except Exception as e:
        raise SyntaxError("Given request body is not valid")

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
        raise SkyflowError("Invalid URL")


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
