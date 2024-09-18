'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import jwt
import datetime
import requests
from warnings import warn
from collections import namedtuple
from skyflow._utils import log_info, InterfaceName, InfoMessages, getMetrics


from skyflow.errors._skyflow_errors import *

ResponseToken = namedtuple('ResponseToken', ['AccessToken', 'TokenType'])
interface = InterfaceName.GENERATE_BEARER_TOKEN


def generate_bearer_token(credentialsFilePath: str) -> ResponseToken:
    '''
    This function is used to get the access token for skyflow Service Accounts.
    `credentialsFilePath` is the file path in string of the credentials file that is downloaded after Service Account creation.

    Response Token is a named tupe with two attributes:
        1. AccessToken: The access token
        2. TokenType: The type of access token (eg: Bearer)
    '''

    log_info(InfoMessages.GENERATE_BEARER_TOKEN_TRIGGERED.value,
             interface=interface)

    try:
        credentialsFile = open(credentialsFilePath, 'r')
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.FILE_NOT_FOUND.value % (credentialsFilePath), interface=interface)

    try:
        credentials = json.load(credentialsFile)
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.FILE_INVALID_JSON.value % (credentialsFilePath), interface=interface)
    finally:
        credentialsFile.close()

    result = getSAToken(credentials)

    log_info(InfoMessages.GENERATE_BEARER_TOKEN_SUCCESS.value,
             interface=interface)
    return result


def generate_bearer_token_from_creds(credentials: str) -> ResponseToken:
    '''
    This function is used to get the access token for skyflow Service Accounts.
    `credentials` arg takes the content of the credentials file that is downloaded after Service Account creation.

    Response Token is a named tupe with two attributes:
        1. AccessToken: The access token
        2. TokenType: The type of access token (eg: Bearer)
    '''

    log_info(InfoMessages.GENERATE_BEARER_TOKEN_TRIGGERED.value,
             interface=interface)
    try:
        jsonCredentials = json.loads(credentials)
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_CREDENTIALS, interface=interface)
    result = getSAToken(jsonCredentials)

    log_info(InfoMessages.GENERATE_BEARER_TOKEN_SUCCESS.value,
             interface=interface)
    return result


def getSAToken(credentials):
    try:
        privateKey = credentials["privateKey"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.MISSING_PRIVATE_KEY, interface=interface)
    try:
        clientID = credentials["clientID"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.MISSING_CLIENT_ID, interface=interface)
    try:
        keyID = credentials["keyID"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.MISSING_KEY_ID, interface=interface)
    try:
        tokenURI = credentials["tokenURI"]
    except:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.MISSING_TOKEN_URI, interface=interface)

    signedToken = getSignedJWT(clientID, keyID, tokenURI, privateKey)

    response = sendRequestWithToken(tokenURI, signedToken)
    content = response.content.decode('utf-8')

    try:
        token = json.loads(content)
    except json.decoder.JSONDecodeError as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.RESPONSE_NOT_JSON % content, interface=interface)
    return getResponseToken(token)


def getSignedJWT(clientID, keyID, tokenURI, privateKey):
    payload = {
        "iss": clientID,
        "key": keyID,
        "aud": tokenURI,
        "sub": clientID,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    try:
        return jwt.encode(payload=payload, key=privateKey, algorithm="RS256")
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.JWT_INVALID_FORMAT, interface=interface)


def sendRequestWithToken(url, token):
    headers = {
        "content-type": "application/json",
        "sky-metadata": json.dumps(getMetrics())
    }
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion":  token
    }
    try:
        response = requests.post(url=url, json=payload, headers=headers)
        statusCode = response.status_code
    except requests.exceptions.InvalidURL:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_URL.value % (url), interface=interface)
    except requests.exceptions.MissingSchema:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.INVALID_URL.value % (url), interface=interface)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        message = SkyflowErrorMessages.API_ERROR.value % statusCode
        if error.response != None and error.response.content != None:
            try:
                errorResponse = json.loads(
                    error.response.content.decode('utf-8'))
                if 'error' in errorResponse and type(errorResponse['error']) == type({}) and 'message' in errorResponse['error']:
                    message = errorResponse['error']['message']
            except:
                message = SkyflowErrorMessages.RESPONSE_NOT_JSON.value % error.response.content.decode(
                    'utf-8')
        if 'x-request-id' in response.headers:
            message += ' - request id: ' + response.headers['x-request-id']
        raise SkyflowError(statusCode, message, interface=interface)

    return response


def getResponseToken(token):
    try:
        accessToken = token["accessToken"]
    except:
        raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR,
                           SkyflowErrorMessages.MISSING_ACCESS_TOKEN, interface=interface)

    try:
        tokenType = token["tokenType"]
    except:
        raise SkyflowError(SkyflowErrorCodes.SERVER_ERROR,
                           SkyflowErrorMessages.MISSING_TOKEN_TYPE, interface=interface)

    return ResponseToken(AccessToken=accessToken, TokenType=tokenType)
