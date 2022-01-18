import types
import requests
from ._insert import getInsertRequestBody, processResponse, convertResponse
from ._config import Configuration
from ._config import InsertOptions, ConnectionConfig
from ._connection import createRequest
from ._detokenize import sendDetokenizeRequests, createDetokenizeResponseBody
from ._getById import sendGetByIdRequests, createGetByIdResponseBody
import asyncio
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow._utils import log_info, InfoMessages, InterfaceName
class Client:
    def __init__(self, config: Configuration):
        
        interface = InterfaceName.CLIENT.value

        log_info(InfoMessages.INITIALIZE_CLIENT.value, interface=interface)

        
        if not isinstance(config.vaultID, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.VAULT_ID_INVALID_TYPE.value%(str(type(config.vaultID))), interface=interface)
        if not isinstance(config.vaultURL, str):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.VAULT_URL_INVALID_TYPE.value%(str(type(config.vaultURL))), interface=interface)

        if not isinstance(config.tokenProvider, types.FunctionType):
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.TOKEN_PROVIDER_ERROR.value%(str(type(config.tokenProvider))), interface=interface)

        self.vaultID = config.vaultID
        self.vaultURL = config.vaultURL.rstrip('/')
        self.tokenProvider = config.tokenProvider
        log_info(InfoMessages.CLIENT_INITIALIZED.value, interface=interface)

    def insert(self, records: dict, options: InsertOptions = InsertOptions()):
        interface = InterfaceName.INSERT.value
        log_info(InfoMessages.INSERT_TRIGGERED.value, interface=interface)

        self._checkConfig(interface)

        jsonBody = getInsertRequestBody(records, options.tokens)
        requestURL = self.vaultURL + "/v1/vaults/" + self.vaultID
        token = self.tokenProvider()
        headers = {
            "Authorization": "Bearer " + token
        }

        response = requests.post(requestURL, data=jsonBody, headers=headers)
        processedResponse = processResponse(response)
        result = convertResponse(records, processedResponse, options.tokens)

        log_info(InfoMessages.INSERT_DATA_SUCCESS.value, interface)
        return result

    def invokeConnection(self, config: ConnectionConfig):
        
        interface = InterfaceName.INVOKE_CONNECTION.value
        log_info(InfoMessages.INVOKE_CONNECTION_TRIGGERED.value, interface)

        self._checkConfig(interface)
        session = requests.Session()
        token = self.tokenProvider()
        request = createRequest(config)

        if not 'X-Skyflow-Authorization' in request.headers.keys():
            request.headers['X-Skyflow-Authorization'] = token

        response = session.send(request)
        session.close()
        return processResponse(response, interface=interface)

    def detokenize(self, records):
        interface = InterfaceName.DETOKENIZE.value
        log_info(InfoMessages.DETOKENIZE_TRIGGERED.value, interface)

        self._checkConfig(interface)
        token = self.tokenProvider()
        url = self.vaultURL + "/v1/vaults/" + self.vaultID + "/detokenize"
        responses = asyncio.run(sendDetokenizeRequests(records, url, token))
        result, partial = createDetokenizeResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS ,SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.DETOKENIZE_SUCCESS.value, interface)
            return result
    
    def getById(self, records):
        interface = InterfaceName.GET_BY_ID.value
        log_info(InfoMessages.GET_BY_ID_TRIGGERED.value, interface)

        self._checkConfig(interface)
        token = self.tokenProvider()
        url = self.vaultURL + "/v1/vaults/" + self.vaultID
        responses = asyncio.run(sendGetByIdRequests(records, url, token))
        result, partial = createGetByIdResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS ,SkyflowErrorMessages.PARTIAL_SUCCESS, result, interface=interface)
        else:
            log_info(InfoMessages.GET_BY_ID_SUCCESS.value, interface)
            return result
        
    def _checkConfig(self, interface):
        if not len(self.vaultID) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_VAULT_ID, interface=interface)
        if not len(self.vaultURL) > 0:
            raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.EMPTY_VAULT_URL, interface=interface)


