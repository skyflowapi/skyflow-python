from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid
from skyflow.Vault import Client, InsertOptions, Configuration

# cached token for reuse
accessToken = ''
def tokenProvider():
    if isValid(accessToken):
        return accessToken
    accessToken, _ = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return accessToken

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

