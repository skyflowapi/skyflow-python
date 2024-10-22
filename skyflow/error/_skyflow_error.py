from skyflow.utils.logger import log_error

class SkyflowError(Exception):
    def __init__(self,
                 message,
                 http_code,
                 request_id = None,
                 grpc_code = None,
                 http_status = None,
                 details = None,
                 logger = None):
        log_error(message, http_code, request_id, grpc_code, http_status, details, logger)
        super().__init__()