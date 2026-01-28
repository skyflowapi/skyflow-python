from ..enums import LogLevel
from . import Logger
from ..constants import ResponseField


def log_info(message, logger = None):
    if not logger:
        logger = Logger(LogLevel.INFO)

    logger.info(message)

def log_error_log(message, logger=None):
    if not logger:
        logger = Logger(LogLevel.ERROR)
    logger.error(message)

def log_error(message, http_code, request_id=None, grpc_code=None, http_status=None, details=None, logger=None):
    if not logger:
        logger = Logger(LogLevel.ERROR)

    log_data = {
        ResponseField.HTTP_CODE: http_code,
        ResponseField.MESSAGE: message
    }

    if grpc_code is not None:
        log_data[ResponseField.GRPC_CODE] = grpc_code
    if http_status is not None:
        log_data[ResponseField.HTTP_STATUS] = http_status
    if request_id is not None:
        log_data[ResponseField.REQUEST_ID] = request_id
    if details is not None:
        log_data[ResponseField.DETAILS] = details

    logger.error(log_data)