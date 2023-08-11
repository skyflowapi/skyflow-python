'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import types
import requests
from skyflow.vault._insert import getInsertRequestBody, processResponse, convertResponse
from skyflow.vault._update import sendUpdateRequests, createUpdateResponseBody
from skyflow.vault._config import Configuration
from skyflow.vault._config import InsertOptions, ConnectionConfig, UpdateOptions
from skyflow.vault._connection import createRequest
from skyflow.vault._detokenize import sendDetokenizeRequests, createDetokenizeResponseBody
from skyflow.vault._get_by_id import sendGetByIdRequests, createGetResponseBody
from skyflow.vault._get import sendGetRequests
import asyncio
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import log_info, InfoMessages, InterfaceName, getMetrics
from ._token import tokenProviderWrapper


class Client:
    '''
    Represents a client for interacting with Skyflow services.

    :param config: Configuration for the Skyflow client.
    '''
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
        '''
        Inserts data into the vault.

        :param records: Records to insert.
        :param options: Options for the insertion.
        :returns: Returns the insert response.
        '''
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

        response = requests.post(requestURL, data=jsonBody, headers=headers)
        processedResponse = processResponse(response)
        result = convertResponse(records, processedResponse, options.tokens)

        log_info(InfoMessages.INSERT_DATA_SUCCESS.value, interface)
        return result

    def detokenize(self, records):
        '''
        Returns values that correspond to the specified tokens.

        :param records: Takes a dictionary that contains the records key that takes an array of records to fetch from the vault.
        :returns: Tokens to return values for.
        '''
        interface = InterfaceName.DETOKENIZE.value
        log_info(InfoMessages.DETOKENIZE_TRIGGERED.value, interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url() + '/detokenize'
        responses = asyncio.run(sendDetokenizeRequests(
            records, url, self.storedToken))
        result, partial = createDetokenizeResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.DETOKENIZE_SUCCESS.value, interface)
            return result

    def get(self, records):
        '''
        Returns records by Skyflow IDs or column values.

        :param records: Takes a Dictionary that contains either an array of Skyflow IDs or a unique column name and values.
        :returns: Returns the specified records and any errors.
        '''
        interface = InterfaceName.GET.value
        log_info(InfoMessages.GET_TRIGGERED.value, interface)

        self._checkConfig(interface)
        self.storedToken = tokenProviderWrapper(
            self.storedToken, self.tokenProvider, interface)
        url = self._get_complete_vault_url()
        responses = asyncio.run(sendGetRequests(
            records, url, self.storedToken))
        result, partial = createGetResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS,
                               SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.GET_SUCCESS.value, interface)

            return result

    def get_by_id(self, records):
        '''
        Reveals records by Skyflow ID.

        :param records: Takes a Dictionary that contains records to fetch.
        :returns: Returns the specified records and any errors.
        '''
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
        '''
        Invokes a connection using the provided configuration.

        :param config: Configuration for the connection.
        :returns: Returns the response from the connection invocation.
        '''
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

    def _checkConfig(self, interface):

        if not len(self.vaultID) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.EMPTY_VAULT_ID, interface=interface)
        if not len(self.vaultURL) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                               SkyflowErrorMessages.EMPTY_VAULT_URL, interface=interface)

    def _get_complete_vault_url(self):

        return self.vaultURL + "/v1/vaults/" + self.vaultID

    def update(self, updateInput, options: UpdateOptions = UpdateOptions()):
        '''
        Updates the configuration of elements in the vault.

        :param updateInput: Input for updating elements in the vault.
        :param options: Options for the container update.
        :returns: Returns the result of the update operation.
        '''
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