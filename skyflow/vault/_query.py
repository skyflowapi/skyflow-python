'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json

import requests
from ._config import QueryOptions
from requests.models import HTTPError
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import InterfaceName

interface = InterfaceName.QUERY.value


def getQueryRequestBody(data, options):
    try:
        query = data["query"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.QUERY_KEY_ERROR, interface=interface)

    if not isinstance(query, str):
        queryType = str(type(query))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_QUERY_TYPE.value % queryType, interface=interface)
    
    if not query.strip():
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,SkyflowErrorMessages.EMPTY_QUERY.value, interface=interface)
        
    requestBody = {"query": query}
    try:
        jsonBody = json.dumps(requestBody)
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_JSON.value % (
            'query payload'), interface=interface)

    return jsonBody

def getQueryResponse(response: requests.Response, interface=interface):
    statusCode = response.status_code
    content = response.content.decode('utf-8')
    try:
        response.raise_for_status()
        try:
            return json.loads(content)
        except:
            raise SkyflowError(
                statusCode, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content, interface=interface)
    except HTTPError:
        message = SkyflowErrorMessages.API_ERROR.value % statusCode
        if response != None and response.content != None:
            try:
                errorResponse = json.loads(content)
                if 'error' in errorResponse and type(errorResponse['error']) == type({}) and 'message' in errorResponse['error']:
                    message = errorResponse['error']['message']
            except:
                message = SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content
                raise SkyflowError(SkyflowErrorCodes.INVALID_INDEX, message, interface=interface)
        error = {"error": {}}
        if 'x-request-id' in response.headers:
            message += ' - request id: ' + response.headers['x-request-id']
            error['error'].update({"code": statusCode, "description": message})
            raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR, SkyflowErrorMessages.SERVER_ERROR.value, error, interface=interface)
