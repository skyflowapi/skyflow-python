import jwt
import time
from skyflow.errors._skyflowerrors import *

def tokenProviderWrapper(storedToken: str, newTokenProvider, interface: str):
    '''
    Check if stored token is not expired, if not return a new token
    '''
    
    if len(storedToken) == 0:
        return newTokenProvider()

    try:
        decoded = jwt.decode(storedToken, options={"verify_signature": False,"verify_aud": False})
        if time.time() + 300 < decoded['exp']:
            return storedToken
    except jwt.ExpiredSignatureError:
        return newTokenProvider()
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.JWT_DECODE_ERROR, interface=interface)