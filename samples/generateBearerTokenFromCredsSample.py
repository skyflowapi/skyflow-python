import json

from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerTokenFromCreds, isValid

'''
    This sample demonstrates the usage of generateBearerTokenFromCreds

    - Use json.dumps(credentialsString) to make it a valid json string
    - Use generateBearerTokenFromCreds(jsonString) to get the Bearer Token
'''

# cache token for reuse
accessToken = ''
def getAccessToken():
    if isValid(accessToken):
        return accessToken

    # As an example
    credentials = {
        "clientID": "<YOUR_clientID>",
        "clientName": "<YOUR_clientName>", 
        "keyID": "<YOUR_keyID>", 
        "tokenURI": '<YOUR_tokenURI>', 
        "privateKey": "<YOUR_PEM_privateKey>"
    }
    jsonString = json.dumps(credentials)
    return generateBearerTokenFromCreds(credentials=jsonString)

try:
    accessToken, tokenType = getAccessToken()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)