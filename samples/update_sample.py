'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, UpdateOptions, Configuration

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
    client = Client(config)

    options = UpdateOptions(True)

    data = {
        "records": [
            {
                "id": "<SKYFLOW_ID>",
                "table": "<TABLE_NAME>",
                "fields": {
                    "<FIELDNAME>": "<VALUE>"
                }
            }
        ]
    }
    response = client.update(data, options=options)
    print('Response:', response)
except SkyflowError as skyflow_error:
    print('Skyflow Error Occurred:', skyflow_error)
except Exception as general_error:
    print('Unexpected Error Occurred:', general_error)
