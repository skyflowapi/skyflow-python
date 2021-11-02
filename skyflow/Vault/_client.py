import requests
from ._insert import getInsertRequestBody, processResponse
from ._config import SkyflowConfiguration
from ._config import InsertOptions
from ._detokenize import sendDetokenizeRequests, createDetokenizeResponseBody
import asyncio
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages   

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

    def detokenize(self, data):
        token = self.tokenProvider()
        url = self.vaultURL + "/v1/vaults/" + self.vaultID + "/detokenize"
        responses = asyncio.run(sendDetokenizeRequests(data, url, token))
        result, partial = createDetokenizeResponseBody(responses)
        if partial:
            raise SkyflowError(SkyflowErrorCodes.PARTIAL_SUCCESS ,SkyflowErrorMessages.PARTIAL_SUCCESS, result)
        else:
            return result
        


