import jwt
import time
from skyflow.Errors._skyflowErrors import *
from skyflow._utils import InterfaceName, log_info, log_error, InfoMessages

def isValid(token: str):
    '''
    Check if stored token is not expired, if not return a new token, 
    if the token has expiry time before 5min of current time, call returns False
    '''
    interface = InterfaceName.IS_TOKEN_VALID.value
    log_info(InfoMessages.IS_TOKEN_VALID_TRIGGERED)
    
    if len(token) == 0:
        log_info(InfoMessages.EMPTY_ACCESS_TOKEN, interface)
        return False

    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        if time.time() < decoded['exp']:
            return True 
    except jwt.ExpiredSignatureError:
        return False 
    except Exception as e:
        log_error(e.message, interface)
        return False