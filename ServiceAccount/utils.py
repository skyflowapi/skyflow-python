from collections import namedtuple
import json
import jwt
import datetime
import requests

ResponseToken = namedtuple('ResponseToken', ['AccessToken', 'TokenType'])

def generateToken(credentialsFilePath):
    credentialsFile = open(credentialsFilePath, 'r')
    credentials = json.load(credentialsFile)


    return getSAToken(credentials)

def getSAToken(credentials):
    privateKey = credentials["privateKey"]
    clientID = credentials["clientID"]
    keyID = credentials["keyID"]
    tokenURI = credentials["tokenURI"]

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
    return jwt.encode(payload=payload, key=privateKey, algorithm="RS256")


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

