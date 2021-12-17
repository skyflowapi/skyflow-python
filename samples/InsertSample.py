from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateBearerToken
from skyflow.Vault import Client, InsertOptions, Configuration


def tokenProvider():
    token, _ = GenerateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return token

try:
    config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
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
    print('Error Occurred:', e)

