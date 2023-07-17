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
    This is the documentation for Client Class

    :param config: This is the description for config parameter
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
        This is the description for insert method

        :param records: This is the description for records parameter
        :param options: This is the description for options parameter
        :returns: This is the description for what the method returns
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
        This is the description for detokenize method

        :param records: This is the description for record parameter
        :returns: This is the description for what the method returns
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
        This is the description for get method

        :param records: This is the description for records parameter
        :returns: This is the description for what the method returns
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
        This is the description for get_by_id method

        :param records: This is the description for records parameter
        :returns: This is the description for what the method returns
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
        This is the description for invoke_connection method

        :param config: This is the description for config parameter
        :returns: This is the description for what the method returns
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
        '''
        Performs basic check on the given client config

        :param interface: This is the description for interface parameter
        :returns: This is the description for what the method returns
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

        :returns: This is the description for what the method returns
        '''
        return self.vaultURL + "/v1/vaults/" + self.vaultID

    def update(self, updateInput, options: UpdateOptions = UpdateOptions()):
        '''
        This is the description for update method

        :param updateInput: This is the description for updateInput parameter
        :param options: This is the description for options parameter
        :returns: This is the description for what the method returns
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