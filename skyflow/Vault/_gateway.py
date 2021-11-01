from requests import exceptions
from ._config import GatewayConfig
from skyflow.Errors._skyflowErrors import *
import requests
from urllib.parse import urlencode, urlunsplit
import json

def createRequest(config: GatewayConfig):
    url = parsePathParams(config.gatewayURL, config.pathParams)

    try:
        header = json.loads(json.dumps(config.requestHeader))
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_HEADERS)

    try:
        jsonData = json.dumps(config.requestBody)
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REQUEST_BODY)

    try:
        return requests.Request(
        method=config.methodName.value,
        url=url,
        data=jsonData,
        headers=config.requestHeader,
        params=config.queryParams
    ).prepare()
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_URL.value%(config.gatewayURL))

def parsePathParams(url, pathParams):
    result = url
    for param, value in pathParams.items():

        if not (isinstance(param, str) and isinstance(value, str)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value%(str(type(param)), str(type(value))))

        result = result.replace('{' + param + '}', value)
        
    return result