from .enums import LogLevel
from . import Logger


def log_info(message, interface, logger = None):
    formatted_message = '{} {}'.format(interface, message)
    logger.info(formatted_message)

def log_error(message, http_code, request_id=None, grpc_code=None, http_status=None, details=None, logger=None):
    if not logger:
        logger = Logger(LogLevel.ERROR)

    log_data = {
        'http_code': http_code,
        'message': message
    }

    if grpc_code is not None:
        log_data['grpc_code'] = grpc_code
    if http_status is not None:
        log_data['http_status'] = http_status
    if request_id is not None:
        log_data['request_id'] = request_id
    if details is not None:
        log_data['details'] = details

    logger.error(log_data)