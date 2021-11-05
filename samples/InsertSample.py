import os
from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateToken
from skyflow.Vault import Client, InsertOptions, SkyflowConfiguration

CREDENTIALS_PATH = os.getenv('CREDENTIALS_FILE_PATH')

def tokenProvider():
    token, _ = GenerateToken(CREDENTIALS_PATH)
    return token

try:
    config = SkyflowConfiguration('<VAULT_ID>', '<VAULT_URL>', tokenProvider)
    client = Client(config)

    options = InsertOptions(True)

    data = {
        "records": [
            {
                "table": "<TABLE_NAME>",
                "fields": {
                    "<FIELDNAME>": "<VALUE>"
                }
            }
        ]
    }
    response = client.insert(data, options=options)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occured:', e)

