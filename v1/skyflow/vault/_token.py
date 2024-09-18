'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import jwt
import time
from skyflow.errors._skyflow_errors import *


def tokenProviderWrapper(storedToken: str, newTokenProvider, interface: str):
    '''
    Check if stored token is not expired, if not return a new token
    '''

    if len(storedToken) == 0:
        newToken = newTokenProvider()
        verify_token_from_provider(newToken, interface)
        return newToken

    try:
        decoded = jwt.decode(storedToken, options={
                             "verify_signature": False, "verify_aud": False})
        if time.time() < decoded['exp']:
            return storedToken
        else:
            newToken = newTokenProvider()
            verify_token_from_provider(newToken, interface)
            return newToken
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.JWT_DECODE_ERROR, interface=interface)


def verify_token_from_provider(token, interface):
    '''
    Verify the jwt from token provider
    '''
    try:
        jwt.decode(token, options={
            "verify_signature": False,
            "verify_aud": False
        }, algorithms=['RS256'])
    except Exception as e:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT,
                           SkyflowErrorMessages.TOKEN_PROVIDER_INVALID_TOKEN, interface=interface)
