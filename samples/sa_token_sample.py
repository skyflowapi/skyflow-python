'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearerToken = ''
tokenType = ''


def token_provider():
    global bearerToken
    global tokenType
    if is_expired(bearerToken):
        bearerToken, tokenType = generate_bearer_token(
            '<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken, tokenType


try:
    accessToken, tokenType = token_provider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
