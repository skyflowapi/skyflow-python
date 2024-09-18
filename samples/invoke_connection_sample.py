'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, Configuration, RequestMethod, ConnectionConfig

'''
This sample is for generating CVV using Skyflow Connection with a third party integration such as VISA
'''

# cache token for reuse
bearerToken = ''


def token_provider():
    global bearerToken
    if is_expired(bearerToken):
        bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken


try:
    config = Configuration(
        '<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', token_provider)
    connectionConfig = ConnectionConfig('<YOUR_CONNECTION_URL>', RequestMethod.POST,
                                        requestHeader={
                                            'Content-Type': 'application/json',
                                            'Authorization': '<YOUR_CONNECTION_BASIC_AUTH>'
                                        },
                                        requestBody=  # For third party integration
                                        {
                                            "expirationDate": {
                                                "mm": "12",
                                                "yy": "22"
                                            }
                                        },
                                        pathParams={'cardID': '<CARD_VALUE>'})  # param as in the example
    client = Client(config)

    response = client.invoke_connection(connectionConfig)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
