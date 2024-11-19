import json
from skyflow.service_account import is_expired, generate_signed_data_tokens, generate_signed_data_tokens_from_creds

file_path = 'CREDENTIALS_FILE_PATH'
bearer_token = ''

skyflow_credentials = {
    'clientID':'<YOUR_CLIENT_ID>',
    'clientName':'<YOUR_CLIENT_NAME>',
    'tokenURI':'<YOUR_TOKEN_URI>',
    'keyID':'<YOUR_KEY_ID>',
    'privateKey':'<YOUR_PRIVATE_KEY>'
}
credentials_string = json.dumps(skyflow_credentials)


options = {
    'ctx': 'CONTEX_ID',
    'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
    'time_to_live': 90 # in seconds
}

# Generate bearer token from credentials file path
if is_expired(bearer_token):
    actual_token, signed_token = generate_signed_data_tokens(
        '<YOUR_CREDENTIALS_FILE_PATH>', options
    )


# Generate bearer token from credentials string
if is_expired(bearer_token):
    actual_token, signed_token = generate_signed_data_tokens_from_creds(
        credentials_string, options
    )