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
    except SkyflowError as skyflow_error:
        print('Skyflow Error Occurred:', skyflow_error)
    except Exception as general_error:
        print('Unexpected Error Occurred:', general_error)

def bulkDetokenize(client, data):
    try:
        response = client.detokenize(data, DetokenizeOptions(continueOnError=False))
        print('Response:', response)
    except SkyflowError as skyflow_error:
        print('Skyflow Error Occurred:', skyflow_error)
    except Exception as general_error:
        print('Unexpected Error Occurred:', general_error)

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
except SkyflowError as skyflow_error:
    print('Skyflow Error Occurred:', skyflow_error)
except Exception as general_error:
    print('Unexpected Error Occurred:', general_error)
