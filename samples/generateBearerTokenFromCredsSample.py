import json

from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token_from_creds, is_expired

'''
    This sample demonstrates the usage of generate_bearer_token_from_creds

    - Use json.dumps(credentialsString) to make it a valid json string
    - Use generate_bearer_token_from_creds(jsonString) to get the Bearer Token
'''

# cache token for reuse
bearerToken = ''
tokenType = ''


def tokenProvider():

    # As an example
    credentials = {
        "clientID": "<YOUR_clientID>",
        "clientName": "<YOUR_clientName>",
        "keyID": "<YOUR_keyID>",
        "tokenURI": '<YOUR_tokenURI>',
        "privateKey": "<YOUR_PEM_privateKey>"
    }
    jsonString = json.dumps(credentials)
    if is_expired(bearerToken):
        bearerToken, tokenType = generate_bearer_token_from_creds(
            credentials=jsonString)

    return bearerToken


try:
    accessToken, tokenType = tokenProvider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
