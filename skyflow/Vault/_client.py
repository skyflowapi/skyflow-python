import requests
from ._insert import getInsertRequestBody, processResponse, convertResponse
from ._config import SkyflowConfiguration
from ._config import InsertOptions, GatewayConfig
from ._gateway import createRequest
class Client:
    def __init__(self, config: SkyflowConfiguration):
        self.vaultID = config.vaultID
        self.vaultURL = config.vaultURL.rstrip('/')
        self.tokenProvider = config.tokenProvider

    def insert(self, data: dict, options: InsertOptions = InsertOptions()):
        jsonBody = getInsertRequestBody(data, options.tokens)
        requestURL = self.vaultURL + "/v1/vaults/" + self.vaultID
        token = self.tokenProvider()
        headers = {
            "Authorization": "Bearer " + token
        }
        response = requests.post(requestURL, data=jsonBody, headers=headers)
        processedResponse = processResponse(response)
        return convertResponse(data, processedResponse, options.tokens)

    def invokeGateway(self, config: GatewayConfig):
        session = requests.Session()
        token = self.tokenProvider()
        request = createRequest(config)
        request.headers['X-Skyflow-Authorization'] = token
        response = session.send(request)
        session.close()
        return processResponse(response)
