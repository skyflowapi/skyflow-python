from skyflow.utils import SkyflowMessages
from skyflow.utils.logger import log_error

class SkyflowError(Exception):
    def __init__(self,
                 message,
                 http_code,
                 request_id = None,
                 grpc_code = None,
                 http_status = None,
                 details = []):
        self.message = message
        self.http_code = http_code
        self.grpc_code = grpc_code
        self.http_status = http_status if http_status else SkyflowMessages.HttpStatus.BAD_REQUEST.value
        self.details = details
        self.request_id = request_id
        log_error(message, http_code, request_id, grpc_code, http_status, details)
        super().__init__()