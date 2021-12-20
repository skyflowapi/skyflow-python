import logging
from enum import Enum

skyflowLog = logging.getLogger('skyflow')

skyflowLog.setLevel(logging.ERROR)

def log_info(message: str, interface: str, args: list=[]):
    formattedMessage = 'INFO: [Skyflow] {} {}'.format(interface.upper(), message.format(args))
    skyflowLog.log(formattedMessage)


def log_debug(message: str, interface: str):
    formattedMessage = 'DEBUG: [Skyflow] {} {}'.format(interface.upper(), message.format(args))
    skyflowLog.debug(formattedMessage)


def log_warn(message: str, interface: str):
    formattedMessage = 'WARN: [Skyflow] {} {}'.format(interface.upper(), message.format(args))
    skyflowLog.warn(formattedMessage)


def log_error(message: str, interface: str):
    formattedMessage = 'ERROR: [Skyflow] {} {}'.format(interface.upper(), message.format(args))
    skyflowLog.error(formattedMessage)


class InfoMessages(Enum):
    INITIALIZE_CLIENT = "Initializing skyflow client"
    CLIENT_INITIALIZED = "Initialized skyflow client successfully"
    VALIDATE_INSERT_RECORDS = "Validating insert records"
    VALIDATE_DETOKENIZE_INPUT = "Validating detokenize input"
    VALIDATE_GET_BY_ID_INPUT = "Validating getByID input"
    VALIDATE_CONNECTION_CONFIG = "Validating connection config"
    INSERT_DATA_SUCCESS = "Data has been inserted successfully."
    DETOKENIZE_SUCCESS = "Data has been detokenized successfully."
    GET_BY_ID_SUCCESS = "Data fetched from ID successfully."
    BEARER_TOKEN_RECEIVED = "tokenProvider returned token successfully."
    INSERT_TRIGGERED = "Insert method triggered."
    DETOKENIZE_TRIGGERED = "Detokenize method triggered."
    GET_BY_ID_TRIGGERED = "Get by ID triggered."
    INVOKE_CONNECTION_TRIGGERED = "Invoke connection triggered."

class InterfaceNames(Enum):
    CLIENT = "CLIENT"
    INSERT = "CLIENT.INSERT"
    DETOKENIZE = "CLIENT.DETOKENIZE"
    GETBYID = "CLIENT.GETBYID"
    INVOKECONNECTION = "CLIENT.INVOKECONNECTION"
    GENERATEBEARERTOKEN = "SERVICEACCOUNT.GENERATEBEARERTOKEN"