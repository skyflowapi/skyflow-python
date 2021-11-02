from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
import asyncio
from aiohttp import ClientSession
import json

def getDetokenizeRequestBody(data):
    try:
        token = data["token"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.TOKEN_KEY_ERROR)
    if not isinstance(token, str):
        tokenType = str(type(token))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TOKEN_TYPE.value%(tokenType))
    requestBody = {"detokenizationParameters": []}
    requestBody["detokenizationParameters"].append({
        "token": token})
    return requestBody

async def sendDetokenizeRequests(data, url, token):
    
    tasks = []

    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.RECORDS_KEY_ERROR)
    if not isinstance(records, list):
        recordsType = str(type(records))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value%(recordsType))
        
    validatedRecords = []
    for record in records:
        requestBody = getDetokenizeRequestBody(record)
        jsonBody = json.dumps(requestBody)
        validatedRecords.append(jsonBody)
    async with ClientSession() as session:
        for record in validatedRecords:
            headers = {
                "Authorization": "Bearer " + token
            }
            task = asyncio.ensure_future(post(url, record, headers, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)
        await session.close()
    return tasks


async def post(url, data, headers, session):
    async with session.post(url, data=data, headers=headers, ssl=False) as response:
        return (await response.read(), response.status)

def createDetokenizeResponseBody(responses):
    result = {
        "success" : [],
        "errors" : []
    }
    for response in responses:
        partial = False
        r = response.result()
        jsonString = r[0].decode('utf8').replace("'",'"')
        jsonRes = json.loads(jsonString)
        status = r[1]

        if status == 200:
            temp = {}
            temp["token"] = jsonRes["records"][0]["token"]
            temp["value"] = jsonRes["records"][0]["value"]
            result["success"].append(temp)
        else:
            temp = {"error": {}}
            temp["error"]["code"] = jsonRes["error"]["http_code"]
            temp["error"]["description"] = jsonRes["error"]["message"]
            result["errors"].append(temp)
            partial = True
    return result, partial
