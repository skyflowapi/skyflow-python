'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json

import requests
from requests.models import HTTPError
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import InterfaceName
from skyflow.vault._config import BYOT, InsertOptions

interface = InterfaceName.INSERT.value


def getInsertRequestBody(data, options: InsertOptions):
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
    for index, record in enumerate(records):
        tableName, fields = getTableAndFields(record)
        postPayload = {
            "tableName": tableName, 
            "fields": fields,
            "method": "POST",
            "quorum": True,
        }  
        validateTokensAndByotMode(record, options.byot)
        if "tokens" in record:
            tokens = getTokens(record)
            postPayload["tokens"] =  tokens
        
        if upsertOptions:
            postPayload["upsert"] = getUpsertColumn(tableName,upsertOptions)
        
        if options.tokens:
            postPayload['tokenization'] = True

        requestPayload.append(postPayload)
    requestBody = {
        "records": requestPayload, 
        "continueOnError": options.continueOnError,
        "byot": options.byot.value
    }
    if options.continueOnError == None:
        requestBody.pop('continueOnError')
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

def validateTokensAndByotMode(record, byot:BYOT):
    
    if not isinstance(byot, BYOT):
        byotType = str(type(byot))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_BYOT_TYPE.value % (byotType), interface=interface)
        
    if byot == BYOT.DISABLE:
        if "tokens" in record:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.TOKENS_PASSED_FOR_BYOT_DISABLE, interface=interface)
    elif "tokens" not in record:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.NO_TOKENS_IN_INSERT.value % byot.value, interface=interface)
    elif byot == BYOT.ENABLE_STRICT:
        tokens = record["tokens"]
        fields = record["fields"]
        if len(tokens) != len(fields):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INSUFFICIENT_TOKENS_PASSED_FOR_BYOT_ENABLE_STRICT, interface=interface)
        
def getTokens(record):
    tokens = record["tokens"]
    if not isinstance(tokens, dict):
        tokensType = str(type(tokens))
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_TOKENS_TYPE.value % (
            tokensType), interface=interface)
    
    if len(tokens) == 0 :
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_TOKENS_IN_INSERT, interface= interface)
    
    fields = record["fields"]
    for tokenKey in tokens:
            if tokenKey not in fields:
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.MISMATCH_OF_FIELDS_AND_TOKENS, interface= interface)
    return tokens

def processResponse(response: requests.Response, interface=interface):
    statusCode = response.status_code
    content = response.content.decode('utf-8')
    try:
        response.raise_for_status()
        try:
            jsonContent = json.loads(content)
            if 'x-request-id' in response.headers:
                requestId = response.headers['x-request-id']
                jsonContent['requestId'] = requestId
            return jsonContent
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


def convertResponse(request: dict, response: dict, options: InsertOptions):
    responseArray = response['responses']
    requestId = response['requestId']
    records = request['records']
    
    if options.continueOnError:
        return buildResponseWithContinueOnError(responseArray, records, options.tokens, requestId)
    
    else:
        return buildResponseWithoutContinueOnError(responseArray, records, options.tokens)

def buildResponseWithContinueOnError(responseArray, records, tokens: bool, requestId):
    partial = False
    errors = []
    result = []
    for idx, response in enumerate(responseArray):
        table = records[idx]['table']
        body = response['Body']
        status = response['Status']
        
        if 'records' in body:
            skyflow_id = body['records'][0]['skyflow_id']
            if tokens:
                fieldsDict = body['records'][0]['tokens']
                fieldsDict['skyflow_id'] = skyflow_id
                result.append({'table': table, 'fields': fieldsDict, 'request_index': idx})
            else:
                result.append({'table': table, 'skyflow_id': skyflow_id, 'request_index': idx})
        elif 'error' in body:
            partial = True
            message = body['error']
            message += ' - request id: ' + requestId
            error = {"code": status, "description": message, "request_index": idx}
            errors.append({"error": error})
    finalResponse = {"records": result, "errors": errors}
    if len(result) == 0:
        partial = False
        finalResponse.pop('records')
    elif len(errors) == 0:
        finalResponse.pop('errors')
    return finalResponse, partial

def buildResponseWithoutContinueOnError(responseArray, records, tokens: bool):
    # recordsSize = len(records)
    result = []
    for idx, _ in enumerate(responseArray):
        table = records[idx]['table']
        skyflow_id = responseArray[idx]['records'][0]['skyflow_id']
        if tokens:
            fieldsDict = responseArray[idx]['records'][0]['tokens']
            fieldsDict['skyflow_id'] = skyflow_id
            result.append({'table': table, 'fields': fieldsDict, 'request_index': idx})
        else:
            result.append({'table': table, 'skyflow_id': skyflow_id, 'request_index': idx})
    return {'records': result}, False

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