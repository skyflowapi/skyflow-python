import json

import requests
from requests.models import HTTPError
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages


def getInsertRequestBody(data, tokens: bool):
    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.RECORDS_KEY_ERROR)

    if not isinstance(records, list):
        recordsType = str(type(records))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value%(recordsType))
        
    requestPayload = []
    insertTokenPayload = []
    for index, record in enumerate(records):
        tableName, fields = getTableAndFields(record)
        requestPayload.append({
                "tableName": tableName,
                "fields": fields,
                "method": "POST",
                "quorum": True})
        if tokens:
            insertTokenPayload.append({
                "method": "GET",
                "tableName": tableName,
                "ID": "$responses." + str(index) + ".records.0.skyflow_id",
                "tokenization": True
            })
    requestBody = {"records": requestPayload + insertTokenPayload}
    try:
        jsonBody = json.dumps(requestBody)
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT ,SkyflowErrorMessages.INVALID_JSON.value%('insert payload'))

    return jsonBody

def getTableAndFields(record):
    try:
        table = record["table"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.TABLE_KEY_ERROR)
    
    if not isinstance(table, str):
        tableType = str(type(table))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TABLE_TYPE.value%(tableType))

    try:
        fields = record["fields"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.FIELDS_KEY_ERROR)

    if not isinstance(fields, dict):
        fieldsType = str(type(table))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value%(fieldsType))

    return (table, fields)

def processResponse(response: requests.Response):
    statusCode = response.status_code
    strcontent = response.content.decode('utf-8')
    try:
        response.raise_for_status()
        return strcontent
    except HTTPError:
        raise SkyflowError(statusCode, strcontent)

