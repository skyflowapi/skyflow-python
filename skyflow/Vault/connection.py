from requests.sessions import PreparedRequest
from ._config import ConnectionConfig
from skyflow.Errors._skyflowErrors import *
import requests
import json

def createRequest(config: ConnectionConfig) -> PreparedRequest:
    url = parsePathParams(config.connectionURL.rstrip('/'), config.pathParams)

    try:
        if isinstance(config.requestHeader, dict):
            header = json.loads(json.dumps(config.requestHeader))
        else:
            raise Exception()
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_HEADERS)

    try:
        if isinstance(config.requestBody, dict):
            jsonData = json.dumps(config.requestBody)
        else:
            raise Exception()
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REQUEST_BODY)

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
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_URL.value%(config.connectionURL))

def parsePathParams(url, pathParams):
    result = url
    for param, value in pathParams.items():
        result = result.replace('{' + param + '}', value)
        
    return result

def verifyParams(queryParams, pathParams):
    if not isinstance(pathParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAMS)
    if not isinstance(queryParams, dict):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAMS)

    for param, value in pathParams.items():
        if not(isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value%(str(type(param)), str(type(value))))

    for param, value in queryParams.items():
        if not isinstance(param, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAM_TYPE.value%(str(type(param)), str(type(value))))
    
    try:
        json.dumps(queryParams)
    except TypeError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_PARAMS)

