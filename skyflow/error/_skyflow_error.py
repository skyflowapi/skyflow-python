from skyflow.utils import SkyflowMessages

class SkyflowError(Exception):
    def __init__(self,
                 message,
                 http_code,
                 request_id = None,
                 grpc_code = None,
                 http_status = None,
                 details = None):
        self.message = message
        self.http_code = http_code
        self.grpc_code = grpc_code
        self.http_status = http_status if http_status else SkyflowMessages.HttpStatus.BAD_REQUEST.value
        self.details = details if details else []
        self.request_id = request_id
        super().__init__(message)