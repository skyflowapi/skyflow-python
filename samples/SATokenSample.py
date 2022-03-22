from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearerToken = ''
tokenType = ''


def tokenProvider():
    if is_expired(bearerToken):
        bearerToken, tokenType = generate_bearer_token(
            '<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken, tokenType


try:
    accessToken, tokenType = tokenProvider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
