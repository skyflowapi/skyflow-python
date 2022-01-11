from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import generateBearerToken


try:
    accessToken, tokenType = generateBearerToken('<YOUR_CREDENTIALS_FILE_PATH>')
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
