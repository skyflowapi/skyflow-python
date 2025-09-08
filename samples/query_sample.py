'''
	Copyright (c) 2022 Skyflow, Inc.
'''

from skyflow import set_log_level, LogLevel
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired
from skyflow.vault import Client, Configuration

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
    
    set_log_level(LogLevel.DEBUG)
    
    data = {
        "query": "<YOUR_SQL_QUERY>"
    }
    response = client.query(data)
    print('Response:', response)
except SkyflowError as skyflow_error:
    print('Skyflow Error Occurred:', skyflow_error)
except Exception as general_error:
    print('Unexpected Error Occurred:', general_error)