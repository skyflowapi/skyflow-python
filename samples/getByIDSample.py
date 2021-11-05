import os
from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateToken
from skyflow.Vault import Client, SkyflowConfiguration, Redaction


def tokenProvider():
    token, _ = GenerateToken('YOUR_CREDENTIALS_FILE_PATH')
    return token

try:
    config = SkyflowConfiguration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
    client = Client(config)

    data = { "records": [
            {
                "ids": ["<SKYFLOW_ID1>", "<SKYFLOW_ID2>", "<SKYFLOW_ID3>"],
                "table": "<TABLE_NAME>",
                "redaction": Redaction.PLAIN_TEXT
            }
        ]}

    response = client.getById(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occured:', e)

