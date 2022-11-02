'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from warnings import warn
import jwt
import time
from skyflow.errors._skyflow_errors import *
from skyflow._utils import InterfaceName, log_info, log_error, InfoMessages


def is_expired(token: str):
    '''
    Check if stored token is not expired, if not return a new token, 
    if the token has expiry time before 5min of current time, call returns False
    '''
    interface = InterfaceName.IS_EXPIRED.value
    log_info(InfoMessages.IS_EXPIRED_TRIGGERED.value, interface=interface)
    if len(token) == 0:
        log_info(InfoMessages.EMPTY_ACCESS_TOKEN, interface=interface)
        return True

    try:
        decoded = jwt.decode(
            token, options={"verify_signature": False, "verify_aud": False})
        if time.time() < decoded['exp']:
            return False
    except jwt.ExpiredSignatureError:
        return True
    except Exception as e:
        log_error(InfoMessages.INVALID_TOKEN.value, interface=interface)
        return True

    return True
