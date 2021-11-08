from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateToken
from skyflow.Vault import Client, Configuration


def tokenProvider():
    token, _ = GenerateToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return token

try:
    config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', tokenProvider)
    client = Client(config)

    data = {"records": [{"<FIELD_NAME>": '<TOKEN>'}]}
    response = client.detokenize(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occured:', e)

