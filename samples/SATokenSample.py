import os
from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateToken

filepath = os.getenv('CREDENTIALS_FILE_PATH')

try:
    accessToken, tokenType = GenerateToken(filepath)
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
