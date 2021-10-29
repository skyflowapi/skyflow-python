import requests
from ._insert import getInsertRequestBody, processResponse
from ._config import SkyflowConfiguration
from ._config import InsertOptions
class Client:
    def __init__(self, config: SkyflowConfiguration):
        self.vaultID = config.vaultID
        self.vaultURL = config.vaultURL
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
        return processedResponse
