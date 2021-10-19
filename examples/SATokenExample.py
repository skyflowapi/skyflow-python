from skyflow.ServiceAccount import GenerateToken

filepath = './credentials.json'
accessToken, tokenType = GenerateToken(filepath)

print("Access Token:", accessToken)
print("Type of token:", tokenType)