from collections import namedtuple
import json
import jwt
import datetime
import requests

ResponseToken = namedtuple('ResponseToken', ['AccessToken', 'TokenType'])

def GenerateToken(credentialsFilePath):
    try:
        credentialsFile = open(credentialsFilePath, 'r')
    except e:
        raise Exception("Credentials file not found")

    try:
        credentials = json.load(credentialsFile)
    except e:
        raise Exception("Credentials file is not in JSON format")


    return getSAToken(credentials)

def getSAToken(credentials):
    try:
        privateKey = credentials["privateKey"]
    except:
        raise Exception("Private key not found in credentials")
    try:
        clientID = credentials["clientID"]
    except:
        raise Exception("Client ID not found in credentials")
    try:
        keyID = credentials["keyID"]
    except:
        raise Exception("Key ID not found in credentials")
    try:
        tokenURI = credentials["tokenURI"]
    except:
        raise Exception("Token URI not found in credentials")

    signedToken = getSignedJWT(clientID, keyID, tokenURI, privateKey)

    response = sendRequestWithToken(tokenURI, signedToken) 

    token = json.loads(response.content)
    return ResponseToken(AccessToken=token["accessToken"], TokenType=token["tokenType"])

def getSignedJWT(clientID, keyID, tokenURI, privateKey):
    payload = {
        "iss": clientID,
		"key": keyID,
		"aud": tokenURI,
		"sub": clientID,
		"exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    try:
        return jwt.encode(payload=payload, key=privateKey, algorithm="RS256")
    except:
        raise Exception("Unable to get a JWT with the given credentials")


def sendRequestWithToken(url, token):
    headers = {
        "content-type": "application/json"
    }
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
		"assertion":  token
    }
    response = requests.post(url=url, json=payload, headers=headers)

    return response

