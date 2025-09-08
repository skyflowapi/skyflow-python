'''
	Copyright (c) 2022 Skyflow, Inc.
'''
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


def token_provider():
    global bearerToken
    global tokenType
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
    accessToken, tokenType = token_provider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as skyflow_error:
    print('Skyflow Error Occurred:', skyflow_error)
except Exception as general_error:
    print('Unexpected Error Occurred:', general_error)
