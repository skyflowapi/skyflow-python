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


# Approach 1: Bearer token with string context
# Use a simple string identifier when your policy references a single context value.
# In your Skyflow policy, reference this as: request.context
def get_bearer_token_with_string_context():
    global bearer_token
    options = {'ctx': 'user_12345'}

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            token, _ = generate_bearer_token(file_path, options)
            bearer_token = token
            return bearer_token
    except Exception as e:
        print(f'Error generating token: {str(e)}')


# Approach 2: Bearer token with JSON object context (dict)
# Use a dict when your policy needs multiple context values for conditional data access.
# Each key maps to a Skyflow CEL policy variable under request.context.*
# For example: request.context.role == "admin" and request.context.department == "finance"
def get_bearer_token_with_object_context():
    global bearer_token
    options = {
        'ctx': {
            'role': 'admin',
            'department': 'finance',
            'user_id': 'user_12345',
        }
    }

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            token, _ = generate_bearer_token(file_path, options)
            bearer_token = token
            return bearer_token
    except Exception as e:
        print(f'Error generating token: {str(e)}')


# Approach 3: Bearer token with string context from credentials string
def get_bearer_token_with_context_from_credentials_string():
    global bearer_token
    options = {'ctx': 'user_12345'}

    try:
        if not is_expired(bearer_token):
            return bearer_token
        else:
            token, _ = generate_bearer_token_from_creds(credentials_string, options)
            bearer_token = token
            return bearer_token
    except Exception as e:
        print(f"Error generating token: {str(e)}")


print("String context:", get_bearer_token_with_string_context())
print("Object context:", get_bearer_token_with_object_context())
print("Creds string:", get_bearer_token_with_context_from_credentials_string())
