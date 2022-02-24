from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid
from skyflow.Vault import Client, Configuration

# cache token for reuse
accessToken = ''
def tokenProvider():
    if isValid(accessToken):
        return accessToken
    accessToken, _ = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return accessToken

try:
    config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
    client = Client(config)

    data = {"records": [{"<FIELD_NAME>": '<TOKEN>'}]}
    response = client.detokenize(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

