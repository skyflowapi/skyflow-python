'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, Configuration
from skyflow.vault import RedactionType
from skyflow.vault._config import DetokenizeOptions

# cache token for reuse
bearerToken = ''


def token_provider():
    global bearerToken
    if is_expired(bearerToken):
        bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken

def detokenize(client, data):
    try:
        response = client.detokenize(data, DetokenizeOptions(continueOnError=True))
        print('Response:', response)
    except SkyflowError as e:
        print('Error Occurred:', e)

def bulkDetokenize(client, data):
    try:
        response = client.detokenize(data, DetokenizeOptions(continueOnError=False))
        print('Response:', response)
    except SkyflowError as e:
        print('Error Occurred:', e)

try:
    config = Configuration(
        '<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', token_provider)
    client = Client(config)

    data = {
        "records": [
            {
                "token": '<TOKEN>',
                "redaction": RedactionType.MASKED
            }, 
            {
                "token": '<TOKEN>',
            }
        ]
    }
    
    detokenize(client, data)
    bulkDetokenize(client, data)
except Exception as e:
    print('Something went wrong:', e)
