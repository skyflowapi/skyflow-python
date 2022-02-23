import jwt
import time
from skyflow.Errors._skyflowErrors import *
from skyflow._utils import InterfaceName

def isTokenValid(token: str):
    '''
    Check if stored token is not expired, if not return a new token, 
    if the token has expiry time before 5min of current time, call returns False
    '''
    interface = InterfaceName.IS_TOKEN_VALID.value
    
    if len(token) == 0:
        return False

    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        if time.time() + 300 < decoded['exp']:
            return True 
    except jwt.ExpiredSignatureError:
        return False 
    except Exception:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.JWT_DECODE_ERROR, interface=interface)