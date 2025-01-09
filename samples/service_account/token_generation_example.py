import json
from skyflow.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

file_path = 'CREDENTIALS_FILE_PATH'
bearer_token = ''

# To generate Bearer Token from credentials string.
skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',
    'clientName': '<YOUR_CLIENT_NAME>',
    'tokenURI': '<YOUR_TOKEN_URI>',
    'keyID': '<YOUR_KEY_ID>',
    'privateKey': '<YOUR_PRIVATE_KEY>',
}
credentials_string = json.dumps(skyflow_credentials)


def get_bearer_token_from_file_path():
    # Generate bearer token from credentials file path.
    global bearer_token

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            token, _ = generate_bearer_token(file_path)
            bearer_token = token
            return bearer_token

    except Exception as e:
        print(f'Error generating token from file path: {str(e)}')


def get_bearer_token_from_credentials_string():
    # Generate bearer token from credentials string.
    global bearer_token
    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            token, _ = generate_bearer_token_from_creds(credentials_string)
            bearer_token = token
            return bearer_token
    except Exception as e:
        print(f"Error generating token from credentials string: {str(e)}")



print(get_bearer_token_from_file_path())

print(get_bearer_token_from_credentials_string())