from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid
from skyflow.Vault import Client, Configuration, RequestMethod, ConnectionConfig

'''
This sample is for generating CVV using Skyflow Connection with a third party integration such as VISA
'''

# cached token for reuse
accessToken = ''
def tokenProvider():
    if isValid(accessToken):
        return accessToken
    accessToken, _ = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return accessToken

try:
    config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
    connectionConfig = ConnectionConfig('<YOUR_CONNECTION_URL>', RequestMethod.POST,
    requestHeader={
                'Content-Type': 'application/json',
                'Authorization': '<YOUR_CONNECTION_BASIC_AUTH>'
    },
    requestBody= # For third party integration
    {
        "expirationDate": {
            "mm": "12",
            "yy": "22"
        }
    },
    pathParams={'cardID': '<CARD_VALUE>'}) # param as in the example
    client = Client(config)

    response = client.invokeConnection(connectionConfig)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

