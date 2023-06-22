'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
import asyncio
from aiohttp import ClientSession
from ._config import RedactionType
from skyflow._utils import InterfaceName, getMetrics
from ._get_by_id import get

interface = InterfaceName.GET.value

def getGetRequestBody(data):
    ids = None
    if "ids" in data:
        ids = data["ids"]
        if not isinstance(ids, list):
            idsType = str(type(ids))
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                            SkyflowErrorMessages.INVALID_IDS_TYPE.value % (idsType), interface=interface)
        for id in ids:
            if not isinstance(id, str):
                idType = str(type(id))
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_ID_TYPE.value % (
                    idType), interface=interface)
    try:
        table = data["table"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.TABLE_KEY_ERROR, interface=interface)
    if not isinstance(table, str):
        tableType = str(type(table))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
            tableType), interface=interface)
    try:
        redaction = data["redaction"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.REDACTION_KEY_ERROR, interface=interface)
    if not isinstance(redaction, RedactionType):
        redactionType = str(type(redaction))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REDACTION_TYPE.value % (
            redactionType), interface=interface)
    
    columnName = None
    if "columnName" in data:   
        columnName = data["columnName"] 
        if not isinstance(columnName, str):
            columnNameType = str(type(columnName))
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_COLUMN_NAME.value % (
            columnNameType), interface=interface)
    
    columnValues = None
    if columnName is not None and "columnValues" in data:   
        columnValues = data["columnValues"]
        if not isinstance(columnValues, list):
            columnValuesType= str(type(columnValues))
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_COLUMN_VALUE.value % (
            columnValuesType), interface=interface)
            
    if(ids is None and (columnName is None or columnValues is None)):
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, 
        SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value, interface= interface)
    return ids, table, redaction.value, columnName, columnValues


async def sendGetRequests(data, url, token):
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
        ids, table, redaction, columnName, columnValues = getGetRequestBody(record)
        validatedRecords.append((ids, table, redaction, columnName, columnValues))
    async with ClientSession() as session:
        for record in validatedRecords:
            ids, table, redaction, columnName, columnValues = record
            headers = {
                "Authorization": "Bearer " + token,
                "sky-metadata": json.dumps(getMetrics())
            }
            params = {"redaction": redaction}
            if ids is not None:
                params["skyflow_ids"] = ids
            if columnName is not None:
                params["column_name"] = columnName
                params["column_values"] = columnValues
            task = asyncio.ensure_future(
                get(url, headers, params, session, record[1]))
            tasks.append(task)
        await asyncio.gather(*tasks)
        await session.close()
    return tasks