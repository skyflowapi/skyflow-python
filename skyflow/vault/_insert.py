'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json

import requests
from requests.models import HTTPError
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import InterfaceName

interface = InterfaceName.INSERT.value


def getInsertRequestBody(data, options):
    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.RECORDS_KEY_ERROR, interface=interface)

    if not isinstance(records, list):
        recordsType = str(type(records))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (
            recordsType), interface=interface)
    
    upsertOptions = options.upsert 
    
    if upsertOptions:
        validateUpsertOptions(upsertOptions=upsertOptions)
            
    requestPayload = []
    insertTokenPayload = []
    for index, record in enumerate(records):
        tableName, fields = getTableAndFields(record)
        postPayload = {"tableName": tableName, "fields": fields,"method": "POST","quorum": True}
        
        if upsertOptions:
            postPayload["upsert"] = getUpsertColumn(tableName,upsertOptions)
        
        requestPayload.append(postPayload)
        if options.tokens:
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
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_JSON.value % (
            'insert payload'), interface=interface)

    return jsonBody


def getTableAndFields(record):
    try:
        table = record["table"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.TABLE_KEY_ERROR, interface=interface)

    if not isinstance(table, str):
        tableType = str(type(table))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
            tableType), interface=interface)

    try:
        fields = record["fields"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.FIELDS_KEY_ERROR, interface=interface)

    if not isinstance(fields, dict):
        fieldsType = str(type(fields))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value % (
            fieldsType), interface=interface)

    return (table, fields)


def processResponse(response: requests.Response, interface=interface):
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
        if 'x-request-id' in response.headers:
            message += ' - request id: ' + response.headers['x-request-id']
        raise SkyflowError(statusCode, message, interface=interface)


def convertResponse(request: dict, response: dict, tokens: bool):
    responseArray = response['responses']
    records = request['records']
    recordsSize = len(records)
    result = []
    for idx, _ in enumerate(records):
        table = records[idx]['table']
        skyflow_id = responseArray[idx]['records'][0]['skyflow_id']
        if tokens:
            fieldsDict = responseArray[recordsSize + idx]['fields']
            fieldsDict['skyflow_id'] = skyflow_id
            result.append({'table': table, 'fields': fieldsDict})
        else:
            result.append({'table': table, 'skyflow_id': skyflow_id})
    return {'records': result}

def getUpsertColumn(tableName, upsertOptions):
    uniqueColumn:str = ''
    for upsertOption in upsertOptions:
        if tableName == upsertOption.table:
            uniqueColumn = upsertOption.column
    return uniqueColumn

def validateUpsertOptions(upsertOptions):
    if not isinstance(upsertOptions,list):
        upsertOptionsType = str(type(upsertOptions))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_UPSERT_OPTIONS_TYPE.value %(
                upsertOptionsType),interface=interface)
    if len(upsertOptions) == 0:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_UPSERT_OPTIONS_LIST.value, interface=interface)
    
    for index, upsertOption in enumerate(upsertOptions):
        if upsertOption.table == None or not isinstance(upsertOption.table,str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_UPSERT_TABLE_TYPE.value %(
                    index),interface=interface)
        if upsertOption.table == '':
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_UPSERT_OPTION_TABLE.value %(
                    index),interface=interface)
        if upsertOption.column == None or not isinstance(upsertOption.column,str):
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_UPSERT_COLUMN_TYPE.value %(
                    index),interface=interface)
        if upsertOption.column == '':
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_UPSERT_OPTION_COLUMN.value %(
                    index),interface=interface)