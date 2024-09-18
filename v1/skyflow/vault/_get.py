'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
import asyncio
from aiohttp import ClientSession
from skyflow.vault._config import RedactionType, GetOptions
from skyflow._utils import InterfaceName, getMetrics
from skyflow.vault._get_by_id import get

interface = InterfaceName.GET.value

def getGetRequestBody(data, options: GetOptions):
    requestBody = {}
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
        requestBody["skyflow_ids"] = ids
    try:
        table = data["table"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.TABLE_KEY_ERROR, interface=interface)
    if not isinstance(table, str):
        tableType = str(type(table))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
            tableType), interface=interface)
    else:
        requestBody["tableName"] = table

    if options.tokens:
        if data.get("redaction"):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                            SkyflowErrorMessages.REDACTION_WITH_TOKENS_NOT_SUPPORTED, interface=interface)
        if (data.get('columnName') or data.get('columnValues')):
            raise SkyflowError(SkyflowErrorCodes.TOKENS_GET_COLUMN_NOT_SUPPORTED,
                           SkyflowErrorMessages.TOKENS_GET_COLUMN_NOT_SUPPORTED, interface=interface)
        requestBody["tokenization"] = options.tokens
    else:
        try:
            redaction = data["redaction"]
        except KeyError:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.REDACTION_KEY_ERROR, interface=interface)
        if not isinstance(redaction, RedactionType):
            redactionType = str(type(redaction))
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_REDACTION_TYPE.value % (
                redactionType), interface=interface)
        else:
            requestBody["redaction"] = redaction.value

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
                columnValuesType = str(type(columnValues))
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_COLUMN_VALUE.value % (
                    columnValuesType), interface=interface)
            else:
                requestBody["column_name"] = columnName
                requestBody["column_values"] = columnValues

        if (ids is None and (columnName is None or columnValues is None)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR, interface=interface)
        elif (ids != None and (columnName != None or columnValues != None)):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.BOTH_IDS_AND_COLUMN_DETAILS_SPECIFIED, interface=interface)
    return requestBody

async def sendGetRequests(data, options: GetOptions, url, token):
    tasks = []
    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(
            SkyflowErrorCodes.INVALID_INPUT,
            SkyflowErrorMessages.RECORDS_KEY_ERROR,
            interface=interface
        )
    if not isinstance(records, list):
        recordsType = str(type(records))
        raise SkyflowError(
            SkyflowErrorCodes.INVALID_INPUT,
            SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % recordsType,
            interface=interface
        )

    validatedRecords = []
    for record in records:
        requestBody = getGetRequestBody(record, options)
        validatedRecords.append(requestBody)
    async with ClientSession() as session:
        for record in validatedRecords:
            headers = {
                "Authorization": "Bearer " + token,
                "sky-metadata": json.dumps(getMetrics())
            }
            table = record.pop("tableName")
            params = record
            if options.tokens:
                params["tokenization"] = json.dumps(record["tokenization"])
            task = asyncio.ensure_future(
                get(url, headers, params, session, table)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)
        await session.close()
    return tasks