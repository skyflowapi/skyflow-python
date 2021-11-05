import os
from skyflow.Errors import SkyflowError
from skyflow.ServiceAccount import GenerateToken


try:
    accessToken, tokenType = GenerateToken('YOUR_CREDENTIALS_FILE_PATH')
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)
