from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid

# cache token for reuse
bearerToken = ''
def tokenProvider():
    if not isValid(bearerToken):
        bearerToken, _ = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken

try:
    accessToken, tokenType = tokenProvider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
