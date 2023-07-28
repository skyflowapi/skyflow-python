'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json

import requests
from requests.models import HTTPError
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import InterfaceName

interface = InterfaceName.DELETE.value


def deleteProcessResponse(response: requests.Response, interface=interface):
    statusCode = response.status_code
    content = response.content
    partial = False
    try:
        response.raise_for_status()
        if statusCode == 204:
            return None
        try:
            return partial,json.loads(content)
        except:
            raise SkyflowError(
                statusCode, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content, interface=interface)
    except HTTPError:
        message = SkyflowErrorMessages.API_ERROR.value % statusCode
        if response is not None and response.content is not None:
            try:
                errorResponse = json.loads(content)
                if 'error' in errorResponse and type(errorResponse['error']) == dict and 'message' in errorResponse[
                    'error']:
                    message = errorResponse['error']['message']
                    partial=True
            except:
                message = SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content
        error = {}
        if 'x-request-id' in response.headers:
            message += ' - request id: ' + response.headers['x-request-id']
            error.update({"code": statusCode, "description": message})
            return partial,error

