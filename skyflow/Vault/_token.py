from pyclbr import Function
import jwt
import time
from skyflow.Errors._skyflowErrors import *

def tokenProviderWrapper(storedToken: str, newTokenProvider: Function, interface: str):
    '''
    Check if stored token is not expired, if not return a new token
    '''
    
    if len(storedToken) == 0:
        return newTokenProvider()

    try:
        decoded = jwt.decode(storedToken, options={"verify_signature": False})
        if time.time() < decoded['exp']:
            return newTokenProvider()
    except jwt.ExpiredSignatureError:
        return newTokenProvider
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.JWT_DECODE_ERROR, interface=interface)