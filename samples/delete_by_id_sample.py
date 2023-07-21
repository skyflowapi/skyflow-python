'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, Configuration,DeleteOptions


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
    options = DeleteOptions(False)

    data = {"records": [
        {
            "id": "<SKYFLOW_ID1>",
            "table": "<TABLE_NAME>",
        },
        {
            "id": "<SKYFLOW_ID2>",
            "table": "<TABLE_NAME>",
        }
    ]}

    response = client.delete_by_id(data,options=options)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
