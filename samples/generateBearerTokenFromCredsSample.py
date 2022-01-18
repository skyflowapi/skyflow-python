import json

from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerTokenFromCreds

'''
    This sample demonstrates the usage of generateBearerTokenFromCreds

    - Use json.dumps(credentialsString) to make it a valid json string
    - Use generateBearerTokenFromCreds(jsonString) to get the Bearer Token
'''


try:
    credentials = {} # Your credentials as a dict e.g. {"clientID": "your_client_ID", tokenURI: 'www.your-token-URI.com', ...}
    jsonString = json.dumps(credentials)
    accessToken, tokenType = generateBearerTokenFromCreds(credentials=jsonString)
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)