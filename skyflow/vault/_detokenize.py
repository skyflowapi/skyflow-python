'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
import asyncio
from aiohttp import ClientSession, request
import json
from ._config import RedactionType
from skyflow._utils import InterfaceName, getMetrics

interface = InterfaceName.DETOKENIZE.value


def getDetokenizeRequestBody(data):
    try:
        token = data["token"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                            SkyflowErrorMessages.TOKEN_KEY_ERROR, interface=interface)
    if not isinstance(token, str):
        tokenType = str(type(token))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TOKEN_TYPE.value % (
            tokenType), interface=interface)

    if "redaction" in data:
        if not isinstance(data["redaction"], RedactionType):
            redactionType = str(type(data["redaction"]))
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REDACTION_TYPE.value % (
            redactionType), interface=interface)
        else:
            redactionType =  data["redaction"]
    else:
        redactionType = RedactionType.PLAIN_TEXT

    requestBody = {"detokenizationParameters": []}
    requestBody["detokenizationParameters"].append({
        "token": token,
        "redaction": redactionType.value
        })
    return requestBody


async def sendDetokenizeRequests(data, url, token):

    tasks = []

    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.RECORDS_KEY_ERROR, interface=interface)
    if not isinstance(records, list):
        recordsType = str(type(records))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (
            recordsType), interface=interface)
    validatedRecords = []
    for record in records:
        requestBody = getDetokenizeRequestBody(record)
        jsonBody = json.dumps(requestBody)
        validatedRecords.append(jsonBody)
    async with ClientSession() as session:
        for record in validatedRecords:
            headers = {
                "Authorization": "Bearer " + token,
                "sky-metadata": json.dumps(getMetrics())

            }
            task = asyncio.ensure_future(post(url, record, headers, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
        await session.close()
    return tasks


async def post(url, data, headers, session):
    async with session.post(url, data=data, headers=headers, ssl=False) as response:
        try:
            return (await response.read(), response.status, response.headers['x-request-id'])
        except KeyError:
            return (await response.read(), response.status)


def createDetokenizeResponseBody(responses):
    result = {
        "records": [],
        "errors": []
    }
    partial = False
    for response in responses:
        r = response.result()
        status = r[1]
        try:
            jsonRes = json.loads(r[0].decode('utf-8'))
        except:
            raise SkyflowError(status,
                               SkyflowErrorMessages.RESPONSE_NOT_JSON.value % r[0].decode('utf-8'), interface=interface)

        if status == 200:
            temp = {}
            temp["token"] = jsonRes["records"][0]["token"]
            temp["value"] = jsonRes["records"][0]["value"]
            result["records"].append(temp)
        else:
            temp = {"error": {}}
            temp["error"]["code"] = jsonRes["error"]["http_code"]
            temp["error"]["description"] = jsonRes["error"]["message"]
            if len(r) > 2 and r[2] != None:
                temp["error"]["description"] += ' - Request ID: ' + str(r[2])
            result["errors"].append(temp)
            partial = True
    return result, partial
