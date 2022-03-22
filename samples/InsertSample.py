from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, InsertOptions, Configuration

# cache token for reuse
bearerToken = ''

def tokenProvider():
    global bearerToken
    if is_expired(bearerToken):
        bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken


try:
    config = Configuration(
        '', '', tokenProvider)
    client = Client(config)

    options = InsertOptions(True)

    data = {
        "records": [
            {
                "table": "cards",
                "fields": {
                    "fullnam": "san"
                }
            }
        ]
    }
    response = client.insert(data, options=options)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
