from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isExpired

# cache token for reuse
bearerToken = ''
tokenType = ''


def tokenProvider():
    if not isExpired(bearerToken):
        bearerToken, tokenType = generateBearerToken(
            '<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken, tokenType


try:
    accessToken, tokenType = tokenProvider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
