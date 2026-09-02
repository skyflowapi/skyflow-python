import json
import threading

from skyflow_flowvault.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
)

# This example generates Bearer Tokens in two ways -- from a file path and from a credentials
# string -- and shows multithreaded token generation with a shared context ('ctx'), where each
# thread generates and prints tokens repeatedly.

file_path = '<YOUR_CREDENTIALS_FILE_PATH>'

skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',
    'clientName': '<YOUR_CLIENT_NAME>',
    'tokenURI': '<YOUR_TOKEN_URI>',
    'keyID': '<YOUR_KEY_ID>',
    'privateKey': '<YOUR_PRIVATE_KEY>',
}
credentials_string = json.dumps(skyflow_credentials)

options = {'ctx': 'abc'}


def generate_from_file_path():
    for _ in range(5):
        try:
            token, _ = generate_bearer_token(file_path, options)
            print(token)
        except Exception as e:
            print(f'Error generating token from file path: {str(e)}')


def generate_from_credentials_string():
    for _ in range(5):
        try:
            token, _ = generate_bearer_token_from_creds(credentials_string, options)
            print(token)
        except Exception as e:
            print(f'Error generating token from credentials string: {str(e)}')


threading.Thread(target=generate_from_file_path).start()
threading.Thread(target=generate_from_credentials_string).start()
