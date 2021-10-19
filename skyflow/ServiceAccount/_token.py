from collections import namedtuple
import json
import jwt
import datetime
import requests
from requests import status_codes

from skyflow.Errors._skyflowErrors import *

ResponseToken = namedtuple('ResponseToken', ['AccessToken', 'TokenType'])

def GenerateToken(credentialsFilePath):
    try:
        credentialsFile = open(credentialsFilePath, 'r')
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.FILE_NOT_FOUND.value % (credentialsFilePath))

    try:
        credentials = json.load(credentialsFile)
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.FILE_INVALID_JSON.value % (credentialsFilePath))
    finally:
        credentialsFile.close()


    return getSAToken(credentials)

def getSAToken(credentials):
    try:
        privateKey = credentials["privateKey"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.MISSING_PRIVATE_KEY)
    try:
        clientID = credentials["clientID"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.MISSING_CLIENT_ID)
    try:
        keyID = credentials["keyID"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.MISSING_KEY_ID)
    try:
        tokenURI = credentials["tokenURI"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.MISSING_TOKEN_URI)

    signedToken = getSignedJWT(clientID, keyID, tokenURI, privateKey)

    response = sendRequestWithToken(tokenURI, signedToken) 

    try:
        token = json.loads(response.content)
    except json.decoder.JSONDecodeError as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, "Unable to parse the response")
    return getResponseToken(token)
    

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
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.JWT_INVALID_FORMAT)


def sendRequestWithToken(url, token):
    headers = {
        "content-type": "application/json"
    }
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
		"assertion":  token
    }
    try:
        response = requests.post(url=url, json=payload, headers=headers)
        statusCode = response.status_code
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.INVALID_URL.value % (url))


    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise SkyflowError(statusCode, error.strerror)

    return response

def getResponseToken(token):
    try:
        accessToken = token["accessToken"]
    except:
        raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR, SkyflowErrorMessages.MISSING_ACCESS_TOKEN)
    
    try:
        tokenType = token["tokenType"]
    except:
        raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR, SkyflowErrorMessages.MISSING_TOKEN_TYPE)

    return ResponseToken(AccessToken=accessToken, TokenType=tokenType)