import json
from skyflow.service_account import (
    is_expired,
    generate_signed_data_tokens,
    generate_signed_data_tokens_from_creds,
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


options = {
    'ctx': 'CONTEXT_ID',
    'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
    'time_to_live': 90,  # in seconds
}

def get_signed_bearer_token_from_file_path():
    # Generate signed bearer token from credentials file path.
    global bearer_token

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            data_token, signed_data_token = generate_signed_data_tokens(file_path, options)
            return data_token, signed_data_token

    except Exception as e:
        print(f'Error generating token from file path: {str(e)}')


def get_signed_bearer_token_from_credentials_string():
    # Generate signed bearer token from credentials string.
    global bearer_token

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            data_token, signed_data_token = generate_signed_data_tokens_from_creds(credentials_string, options)
            return data_token, signed_data_token

    except Exception as e:
        print(f'Error generating token from credentials string: {str(e)}')


print(get_signed_bearer_token_from_file_path())

print(get_signed_bearer_token_from_credentials_string())
