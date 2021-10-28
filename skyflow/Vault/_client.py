import json
import requests
from ._insert import getInsertRequestBody

class Client:
    def __init__(self, vaultID, vaultURL, tokenProvider):
        self.vaultID = vaultID
        self.vaultURL = vaultURL
        self.tokenProvider = tokenProvider

    def insert(self, data):
        requestBody = getInsertRequestBody(data)
        jsonBody = json.dumps(requestBody)
        requestURL = self.vaultURL + "/v1/vaults/" + self.vaultID
        token = self.tokenProvider()
        headers = {
            "Authorization": "Bearer " + token
        }
        response = requests.post(requestURL, data=jsonBody, headers=headers)
        return response
