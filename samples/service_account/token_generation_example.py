import json
from skyflow.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

file_path = 'CREDENTIALS_FILE_PATH'
bearer_token = ''

skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',
    'clientName': '<YOUR_CLIENT_NAME>',
    'tokenURI': '<YOUR_TOKEN_URI>',
    'keyID': '<YOUR_KEY_ID>',
    'privateKey': '<YOUR_PRIVATE_KEY>',
}
credentials_string = json.dumps(skyflow_credentials)


# Generate bearer token from credentials file path
if is_expired(bearer_token):
    bearer_token, token_type = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')

    print(bearer_token, token_type)


# Generate bearer token from credentials string
if is_expired(bearer_token):
    bearer_token, token_type = generate_bearer_token_from_creds(credentials_string)

    print(bearer_token, token_type)
