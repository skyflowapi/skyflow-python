class SkyflowError(Exception):
    def __init__(self,
                 message,
                 http_code,
                 request_id = None,
                 grpc_code = None,
                 http_status = None,
                 details = None,
                 logger = None,
                 logger_method = None):

        logger_method(message, http_code, request_id, grpc_code, http_status, details, logger)
        super().__init__()