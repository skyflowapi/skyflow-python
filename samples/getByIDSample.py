from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid
from skyflow.Vault import Client, Configuration, RedactionType


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

    data = { "records": [
            {
                "ids": ["<SKYFLOW_ID1>", "<SKYFLOW_ID2>", "<SKYFLOW_ID3>"],
                "table": "<TABLE_NAME>",
                "redaction": RedactionType.PLAIN_TEXT
            }
        ]}

    response = client.getById(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

