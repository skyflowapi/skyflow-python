from warnings import warn
import jwt
import time
from skyflow.Errors._skyflowErrors import *
from skyflow._utils import InterfaceName, log_info, log_error, InfoMessages


def isExpired(token: str):
    '''
    Check if stored token is not expired, if not return a new token, 
    if the token has expiry time before 5min of current time, call returns False
    '''
    interface = InterfaceName.IS_EXPIRED.value
    log_info(InfoMessages.IS_EXPIRED_TRIGGERED.value, interface)

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
        log_error(InfoMessages.INVALID_TOKEN.value, interface)
        return False


def isValid(token: str):
    '''
    Check if stored token is not expired, if not return a new token
    if the token has expiry time before 5min of current time, call returns False
    Warning: This function has been deprecated and replaced with isExpired(token: str)
    '''
    warn(
        'This function has been deprecated and replaced with isExpired(token: str)',
        DeprecationWarning)
    interface = InterfaceName.IS_TOKEN_VALID.value
    log_info(InfoMessages.IS_TOKEN_VALID_TRIGGERED.value, interface)

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
        log_error(InfoMessages.INVALID_TOKEN.value, interface)
        return False
