'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import types
import requests
import asyncio
from skyflow.vault._insert import getInsertRequestBody, processResponse, convertResponse
from skyflow.vault._update import sendUpdateRequests, createUpdateResponseBody
from skyflow.vault._config import Configuration, ConnectionConfig, DeleteOptions, DetokenizeOptions, GetOptions, InsertOptions, UpdateOptions, QueryOptions
from skyflow.vault._connection import createRequest
from skyflow.vault._detokenize import sendDetokenizeRequests, createDetokenizeResponseBody
from skyflow.vault._get_by_id import sendGetByIdRequests, createGetResponseBody
from skyflow.vault._get import sendGetRequests
from skyflow.vault._delete import deleteProcessResponse
from skyflow.vault._query import getQueryRequestBody, getQueryResponse
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import log_info, log_error, InfoMessages, InterfaceName, getMetrics
from skyflow.vault._token import tokenProviderWrapper

class Client:
    def __init__(self, config: Configuration):

        interface = InterfaceName.CLIENT.value

        log_info(InfoMessages.INITIALIZE_CLIENT.value, interface=interface)

        if not isinstance(config.vaultID, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.VAULT_ID_INVALID_TYPE.value % (
                str(type(config.vaultID))), interface=interface)
        if not isinstance(config.vaultURL, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.VAULT_URL_INVALID_TYPE.value % (
                str(type(config.vaultURL))), interface=interface)

        if not isinstance(config.tokenProvider, types.FunctionType):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.TOKEN_PROVIDER_ERROR.value % (
                str(type(config.tokenProvider))), interface=interface)

        self.vaultID = config.vaultID
        self.vaultURL = config.vaultURL.rstrip('/')
        self.tokenProvider = config.tokenProvider
        self.storedToken = ''
        log_info(InfoMessages.CLIENT_INITIALIZED.value, interface=interface)

    def insert(self, records: dict, options: InsertOptions = InsertOptions()):
        interface = InterfaceName.INSERT.value
        log_info(InfoMessages.INSERT_TRIGGERED.value, interface=interface)
        self._checkConfig(interface)
        jsonBody = getInsertRequestBody(records, options)
        requestURL = self._get_complete_vault_url()
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        headers = {
            "Authorization": "Bearer " + self.storedToken,
            "sky-metadata": json.dumps(getMetrics())
        }
        max_retries = 3
        # Use for-loop for retry logic, avoid code repetition
        for attempt in range(max_retries+1):
            try:
                # If jsonBody is a dict, use json=, else use data=
                response = requests.post(requestURL, data=jsonBody, headers=headers)
                processedResponse = processResponse(response)
                result, partial = convertResponse(records, processedResponse, options)
                if partial:
                    log_error(SkyflowErrorMessages.BATCH_INSERT_PARTIAL_SUCCESS.value, interface)
                elif 'records' not in result:
                    log_error(SkyflowErrorMessages.BATCH_INSERT_FAILURE.value, interface)
                else:
                    log_info(InfoMessages.INSERT_DATA_SUCCESS.value, interface)
                return result
            except Exception as err:
                if attempt < max_retries:
                    continue
                else:
                    if isinstance(err, SkyflowError):
                        raise err
                    else:
                        raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR, f"Error occurred: {err}", interface=interface)

    def detokenize(self, records: dict, options: DetokenizeOptions = DetokenizeOptions()):
        interface = InterfaceName.DETOKENIZE.value
        log_info(InfoMessages.DETOKENIZE_TRIGGERED.value, interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url() + '/detokenize'
        responses = asyncio.run(sendDetokenizeRequests(
            records, url, self.storedToken, options))
        result, partial = createDetokenizeResponseBody(records, responses, options)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS, SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        elif 'records' not in result:
            raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR, SkyflowErrorMessages.SERVER_ERROR, result, interface=interface)
        else:
            log_info(InfoMessages.DETOKENIZE_SUCCESS.value, interface)
            return result

    def get(self, records, options: GetOptions = GetOptions()):
        interface = InterfaceName.GET.value
        log_info(InfoMessages.GET_TRIGGERED.value, interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url()
        responses = asyncio.run(sendGetRequests(
            records, options, url, self.storedToken))
        result, partial = createGetResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.GET_SUCCESS.value, interface)

            return result

    def get_by_id(self, records):
        interface = InterfaceName.GET_BY_ID.value
        log_info(InfoMessages.GET_BY_ID_TRIGGERED.value, interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url()
        responses = asyncio.run(sendGetByIdRequests(
            records, url, self.storedToken))
        result, partial = createGetResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.GET_BY_ID_SUCCESS.value, interface)

            return result

    def invoke_connection(self, config: ConnectionConfig):

        interface = InterfaceName.INVOKE_CONNECTION.value
        log_info(InfoMessages.INVOKE_CONNECTION_TRIGGERED.value, interface)

        session = requests.Session()
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        request = createRequest(config)

        if not 'X-Skyflow-Authorization'.lower() in request.headers:
            request.headers['x-skyflow-authorization'] = self.storedToken

        request.headers['sky-metadata'] = json.dumps(getMetrics())

        response = session.send(request)
        session.close()
        return processResponse(response, interface=interface)

    def query(self, queryInput, options: QueryOptions = QueryOptions()):
        interface = InterfaceName.QUERY.value
        log_info(InfoMessages.QUERY_TRIGGERED.value, interface=interface)

        self._checkConfig(interface)
        
        jsonBody = getQueryRequestBody(queryInput, options)
        requestURL = self._get_complete_vault_url() + "/query"
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.storedToken,
            "sky-metadata": json.dumps(getMetrics())
        }
        
        response = requests.post(requestURL, data=jsonBody, headers=headers)
        result = getQueryResponse(response)

        log_info(InfoMessages.QUERY_SUCCESS.value, interface)
        return result
    
    def _checkConfig(self, interface):
        '''
            Performs basic check on the given client config
        '''
        if not len(self.vaultID) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.EMPTY_VAULT_ID, interface=interface)
        if not len(self.vaultURL) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.EMPTY_VAULT_URL, interface=interface)

    def _get_complete_vault_url(self):
        '''
            Get the complete vault url from given vault url and vault id
        '''
        return self.vaultURL + "/v1/vaults/" + self.vaultID

    def update(self, updateInput, options: UpdateOptions = UpdateOptions()):
        interface = InterfaceName.UPDATE.value
        log_info(InfoMessages.UPDATE_TRIGGERED.value, interface=interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url()
        responses = asyncio.run(sendUpdateRequests(
            updateInput, options, url, self.storedToken))
        result, partial = createUpdateResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.UPDATE_DATA_SUCCESS.value, interface)
            return result

    def delete(self, records: dict, options: DeleteOptions = DeleteOptions()):
        interface = InterfaceName.DELETE.value
        log_info(InfoMessages.DELETE_TRIGGERED.value, interface=interface)

        self._checkConfig(interface)

        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        headers = {
            "Authorization": "Bearer " + self.storedToken,
            "sky-metadata": json.dumps(getMetrics())
        }
        error_list = []
        result_list = []
        errors = {}
        result = {}
        try:
            record = records["records"]
            if not isinstance(record, list):
                recordsType = str(type(record))
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (
                    recordsType), interface=interface)
            if len(record) == 0:
                raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                                   SkyflowErrorMessages.EMPTY_RECORDS_IN_DELETE, interface=interface)

        except KeyError:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.RECORDS_KEY_ERROR, interface=interface)
        try:
            for record in records["records"]:
                id = record["id"]
                if not isinstance(id, str):
                    idType = str(type(id))
                    raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                                       SkyflowErrorMessages.INVALID_ID_TYPE.value % (idType), interface=interface)
                if id == "":
                    raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                                       SkyflowErrorMessages.EMPTY_ID_IN_DELETE, interface=interface)
        except KeyError:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.IDS_KEY_ERROR, interface=interface)
        try:
            for record in records["records"]:
                table = record["table"]
                if not isinstance(table, str):
                    tableType = str(type(table))
                    raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                                       SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
                                           tableType), interface=interface)
                if table == "":
                    raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                                       SkyflowErrorMessages.EMPTY_TABLE_IN_DELETE, interface=interface)
        except KeyError:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.TABLE_KEY_ERROR, interface=interface)

        partial=None

        for record in records["records"]:
            request_url = self._get_complete_vault_url() + "/" + record["table"] + "/" + record["id"]
            response = requests.delete(request_url, headers=headers)
            partial,processed_response = deleteProcessResponse(response, records)
            if processed_response is not None and processed_response.get('code') == 404:
                errors.update({'id': record["id"], 'error': processed_response})
                error_list.append(errors)
            else:
                result_list.append(processed_response)
        if result_list:
            result.update({'records': result_list})
        if errors:
            result.update({'errors': error_list})

        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)

        else:
            log_info(InfoMessages.DELETE_DATA_SUCCESS.value, interface)
            return result