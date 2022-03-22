from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, Configuration, RedactionType


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

    data = {"records": [
        {
            "ids": ["<SKYFLOW_ID1>", "<SKYFLOW_ID2>", "<SKYFLOW_ID3>"],
            "table": "<TABLE_NAME>",
            "redaction": RedactionType.PLAIN_TEXT
        }
    ]}

    response = client.get_by_id(data)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
