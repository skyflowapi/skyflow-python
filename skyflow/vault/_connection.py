'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from requests.sessions import PreparedRequest
from ._config import ConnectionConfig
from skyflow.errors._skyflow_errors import *
import requests
import json

from skyflow._utils import InterfaceName, http_build_query, supported_content_types, r_urlencode

interface = InterfaceName.INVOKE_CONNECTION.value


def createRequest(config: ConnectionConfig) -> PreparedRequest:
    url = parsePathParams(config.connectionURL.rstrip('/'), config.pathParams)

    try:
        if isinstance(config.requestHeader, dict):
            header = to_lowercase_keys(json.loads(
                json.dumps(config.requestHeader)))
        else:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.INVALID_REQUEST_BODY, interface=interface)
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_HEADERS, interface=interface)
    if not 'Content-Type'.lower() in header:
        header['content-type'] = supported_content_types["JSON"]

    try:
        if isinstance(config.requestBody, dict):
            json_data, files = get_data_from_content_type(
                config.requestBody, header["content-type"])
        else:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.INVALID_RESPONSE_BODY, interface=interface)
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_REQUEST_BODY, interface=interface)

    verifyParams(config.queryParams, config.pathParams)

    try:
        return requests.Request(
            method=config.methodName.value,
            url=url,
            data=json_data,
            headers=header,
            params=config.queryParams,
            files=files
        ).prepare()
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_URL.value % (
            config.connectionURL), interface=interface)


def parsePathParams(url, pathParams):
    result = url
    for param, value in pathParams.items():
        result = result.replace('{' + param + '}', value)

    return result


def verifyParams(queryParams, pathParams):
    if not isinstance(pathParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_PATH_PARAMS, interface=interface)
    if not isinstance(queryParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_QUERY_PARAMS, interface=interface)

    for param, value in pathParams.items():
        if not(isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value % (
                str(type(param)), str(type(value))), interface=interface)

    for param, value in queryParams.items():
        if not isinstance(param, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAM_TYPE.value % (
                str(type(param)), str(type(value))), interface=interface)

    try:
        json.dumps(queryParams)
    except TypeError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_QUERY_PARAMS, interface=interface)


def to_lowercase_keys(dict):
    '''
        convert keys of dictionary to lowercase
    '''
    result = {}
    for key, value in dict.items():
        result[key.lower()] = value

    return result


def get_data_from_content_type(data, content_type):
    '''
        Get request data according to content type
    '''
    converted_data = data
    files = {}
    if content_type == supported_content_types["URLENCODED"]:
        converted_data = http_build_query(data)
    elif content_type == supported_content_types["FORMDATA"]:
        converted_data = r_urlencode(list(), dict(), data)
        files = {(None, None)}
    elif content_type == supported_content_types["JSON"]:
        converted_data = json.dumps(data)

    return converted_data, files
