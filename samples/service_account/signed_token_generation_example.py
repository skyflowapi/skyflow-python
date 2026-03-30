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


# Approach 1: Signed data tokens with string context
def get_signed_tokens_with_string_context():
    options = {
        'ctx': 'user_12345',
        'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
        'time_to_live': 90,  # in seconds
    }
    try:
        data_token, signed_data_token = generate_signed_data_tokens(file_path, options)
        return data_token, signed_data_token
    except Exception as e:
        print(f'Error: {str(e)}')


# Approach 2: Signed data tokens with JSON object context (dict)
# Each key maps to a Skyflow CEL policy variable under request.context.*
# For example: request.context.role == "analyst" and request.context.department == "research"
def get_signed_tokens_with_object_context():
    options = {
        'ctx': {
            'role': 'analyst',
            'department': 'research',
            'user_id': 'user_67890',
        },
        'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
        'time_to_live': 90,
    }
    try:
        data_token, signed_data_token = generate_signed_data_tokens(file_path, options)
        return data_token, signed_data_token
    except Exception as e:
        print(f'Error: {str(e)}')


# Approach 3: Signed data tokens from credentials string
def get_signed_tokens_from_credentials_string():
    options = {
        'ctx': 'user_12345',
        'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
        'time_to_live': 90,
    }
    try:
        data_token, signed_data_token = generate_signed_data_tokens_from_creds(credentials_string, options)
        return data_token, signed_data_token
    except Exception as e:
        print(f'Error: {str(e)}')


print("String context:", get_signed_tokens_with_string_context())
print("Object context:", get_signed_tokens_with_object_context())
print("Creds string:", get_signed_tokens_from_credentials_string())
