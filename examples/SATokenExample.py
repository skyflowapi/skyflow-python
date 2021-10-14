from ServiceAccount import generateToken

filepath = ''
accessToken, tokenType = generateToken(filepath)

print("Access Token:", accessToken)
print("Type of token:", tokenType)