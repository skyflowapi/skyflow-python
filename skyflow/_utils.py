'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import urllib.parse
import logging
from enum import Enum
import platform
import sys
from skyflow.version import SDK_VERSION

skyflowLog = logging.getLogger('skyflow')
skyflowLog.setLevel(logging.ERROR)

supported_content_types = {
    "JSON": 'application/json',
    "PLAINTEXT": 'text/plain',
    "XML": 'text/xml',
    "URLENCODED": 'application/x-www-form-urlencoded',
    "FORMDATA": 'multipart/form-data',
}


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    OFF = logging.CRITICAL


def set_log_level(logLevel: LogLevel):
    '''
    Sets the Log Level for the Skyflow python SDK
    '''
    skyflowLog.setLevel(logLevel.value)


def log_info(message: str, interface: str):
    formattedMessage = '{} {}'.format(interface, message)
    skyflowLog.info(formattedMessage)


# def log_debug(message: str, interface: str):
#     formattedMessage = '{} {}'.format(interface, message)
#     skyflowLog.debug(formattedMessage)


def log_error(message: str, interface: str):
    formattedMessage = '{} {}'.format(interface, message)
    skyflowLog.error(formattedMessage)


class InfoMessages(Enum):
    INITIALIZE_CLIENT = "Initializing skyflow client"
    CLIENT_INITIALIZED = "Initialized skyflow client successfully"
    VALIDATE_INSERT_RECORDS = "Validating insert records"
    VALIDATE_DETOKENIZE_INPUT = "Validating detokenize input"
    VALIDATE_GET_BY_ID_INPUT = "Validating getByID input"
    VALIDATE_CONNECTION_CONFIG = "Validating connection config"
    INSERT_DATA_SUCCESS = "Data has been inserted successfully."
    DETOKENIZE_SUCCESS = "Data has been detokenized successfully."
    GET_BY_ID_SUCCESS = "Data fetched from ID successfully."
    BEARER_TOKEN_RECEIVED = "tokenProvider returned token successfully."
    INSERT_TRIGGERED = "Insert method triggered."
    DETOKENIZE_TRIGGERED = "Detokenize method triggered."
    GET_BY_ID_TRIGGERED = "Get by ID triggered."
    INVOKE_CONNECTION_TRIGGERED = "Invoke connection triggered."
    GENERATE_BEARER_TOKEN_TRIGGERED = "Generate bearer token triggered"
    GENERATE_BEARER_TOKEN_SUCCESS = "Generate bearer token returned successfully"
    IS_TOKEN_VALID_TRIGGERED = "isTokenValid() triggered"
    IS_EXPIRED_TRIGGERED = "is_expired() triggered"
    EMPTY_ACCESS_TOKEN = "Give access token is empty"
    INVALID_TOKEN = "Given token is invalid"
    UPDATE_TRIGGERED = "Update method triggered"
    UPDATE_DATA_SUCCESS = "Data has been updated successfully"
    GET_TRIGGERED = "Get triggered."
    GET_SUCCESS = "Data fetched successfully."
    DELETE_TRIGGERED = "Delete triggered."
    DELETE_DATA_SUCCESS = "Data has been deleted successfully."


class InterfaceName(Enum):
    CLIENT = "client"
    INSERT = "client.insert"
    DETOKENIZE = "client.detokenize"
    GET_BY_ID = "client.get_by_id"
    GET = "client.get"
    UPDATE = "client.update"
    INVOKE_CONNECTION = "client.invoke_connection"
    GENERATE_BEARER_TOKEN = "service_account.generate_bearer_token"

    IS_TOKEN_VALID = "service_account.isTokenValid"
    IS_EXPIRED = "service_account.is_expired"
    DELETE = "client.delete"


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
    depth, outStr = 0, ''
    for x in parents:
        s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
        outStr += s % str(x)
        depth += 1
    return outStr

def getMetrics():
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