import json
from skyflow_flowvault.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

file_path = '<YOUR_CREDENTIALS_FILE_PATH>'
bearer_token = ''

# To generate a Bearer Token from a credentials string.
skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',
    'clientName': '<YOUR_CLIENT_NAME>',
    'tokenURI': '<YOUR_TOKEN_URI>',
    'keyID': '<YOUR_KEY_ID>',
    'privateKey': '<YOUR_PRIVATE_KEY>',
}
credentials_string = json.dumps(skyflow_credentials)


def get_bearer_token_from_file_path():
    # Generate a Bearer Token from a credentials file path. Reuse it until it expires.
    global bearer_token
    try:
        if not is_expired(bearer_token):
            return bearer_token
        token, _ = generate_bearer_token(file_path)
        bearer_token = token
        return bearer_token
    except Exception as e:
        print(f'Error generating token from file path: {str(e)}')


def get_bearer_token_from_credentials_string():
    # Generate a Bearer Token from a credentials string.
    global bearer_token
    try:
        if not is_expired(bearer_token):
            return bearer_token
        token, _ = generate_bearer_token_from_creds(credentials_string)
        bearer_token = token
        return bearer_token
    except Exception as e:
        print(f'Error generating token from credentials string: {str(e)}')


print('Generated Bearer Token (from file):', get_bearer_token_from_file_path())
print('Generated Bearer Token (from string):', get_bearer_token_from_credentials_string())
