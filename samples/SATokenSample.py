from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken, isValid

# cached token for reuse
accessToken = ''
def getAccessToken():
    if isValid(accessToken):
        return accessToken
    accessToken, tokenType = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')

try:
    accessToken, tokenType = getAccessToken()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
