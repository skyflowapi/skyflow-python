'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json

import asyncio
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from ._insert import getTableAndFields
from skyflow._utils import InterfaceName, getMetrics
from aiohttp import ClientSession
from ._config import UpdateOptions

interface = InterfaceName.UPDATE.value

async def sendUpdateRequests(data,options: UpdateOptions,url,token):
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
        tableName = validateUpdateRecord(record)
        validatedRecords.append(record)
    async with ClientSession() as session:
        for record in validatedRecords:
            recordUrl = url +'/'+ tableName +'/'+ record["id"]
            reqBody = {
                "record": {
                    "fields": record["fields"]
                },
                "tokenization": options.tokens
            }
            reqBody = json.dumps(reqBody)
            headers = {
                "Authorization": "Bearer " + token,
                "sky-metadata": json.dumps(getMetrics())
            }
            task = asyncio.ensure_future(put(recordUrl, reqBody, headers, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
        await session.close()
    return tasks

def validateUpdateRecord(record):
    try:
        id = record["id"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.IDS_KEY_ERROR, interface=interface)
    if not isinstance(id, str):
        idType = str(type(id))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_ID_TYPE.value % (idType), interface=interface)
    table, fields = getTableAndFields(record)
    keysLength = len(fields.keys())
    if(keysLength < 1):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                            SkyflowErrorMessages.UPDATE_FIELD_KEY_ERROR, interface= interface)
    return table

async def put(url, data, headers, session):
    async with session.put(url, data=data, headers=headers, ssl=False) as response:
        try:
            return (await response.read(), response.status, response.headers['x-request-id'])
        except KeyError:
            return (await response.read(), response.status)


def createUpdateResponseBody(responses):
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
            temp["id"] = jsonRes["skyflow_id"]
            if "tokens" in jsonRes:
                temp["fields"] = jsonRes["tokens"]
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
