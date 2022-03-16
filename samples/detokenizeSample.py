from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isExpired
from skyflow.Vault import Client, Configuration

# cache token for reuse
bearerToken = ''


def tokenProvider():
    if isExpired(bearerToken):
        bearerToken, _ = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken


try:
    config = Configuration(
        '<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
    client = Client(config)

    data = {"records": [{"<FIELD_NAME>": '<TOKEN>'}]}
    response = client.detokenize(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
