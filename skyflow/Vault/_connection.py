from requests.sessions import PreparedRequest
from ._config import ConnectionConfig
from skyflow.Errors._skyflowErrors import *
import requests
import json
from skyflow._utils import InterfaceName

interface = InterfaceName.INVOKE_CONNECTION.value

def createRequest(config: ConnectionConfig) -> PreparedRequest:
    url = parsePathParams(config.connectionURL.rstrip('/'), config.pathParams)

    try:
        if isinstance(config.requestHeader, dict):
            header = json.loads(json.dumps(config.requestHeader))
        else:
            raise Exception()
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_HEADERS, interface=interface)

    try:
        if isinstance(config.requestBody, dict):
            jsonData = json.dumps(config.requestBody)
        else:
            raise Exception()
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REQUEST_BODY, interface=interface)

    verifyParams(config.queryParams, config.pathParams)

    try:
        return requests.Request(
        method=config.methodName.value,
        url=url,
        data=jsonData,
        headers=header,
        params=config.queryParams
    ).prepare()
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_URL.value%(config.connectionURL), interface=interface)

def parsePathParams(url, pathParams):
    result = url
    for param, value in pathParams.items():
        result = result.replace('{' + param + '}', value)
        
    return result

def verifyParams(queryParams, pathParams):
    if not isinstance(pathParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAMS, interface=interface)
    if not isinstance(queryParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAMS, interface=interface)

    for param, value in pathParams.items():
        if not(isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value%(str(type(param)), str(type(value))), interface=interface)

    for param, value in queryParams.items():
        if not isinstance(param, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAM_TYPE.value%(str(type(param)), str(type(value))), interface=interface)
    
    try:
        json.dumps(queryParams)
    except TypeError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAMS, interface=interface)

