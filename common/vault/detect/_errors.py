from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.generated.rest.core import ApiError, ParsingError

from ._constants import (
    REQUEST_ID_HEADER,
    ERROR_BODY_KEY,
    ERROR_MESSAGE_KEY,
    ERROR_GRPC_CODE_KEY,
    ERROR_GRPC_CODE_CAMEL_KEY,
    ERROR_HTTP_STATUS_KEY,
    ERROR_HTTP_STATUS_CAMEL_KEY,
    ERROR_DETAILS_KEY,
    UNKNOWN_ERROR_MESSAGE,
)


def extract_request_id(headers):
    return headers.get(REQUEST_ID_HEADER) if headers else None


def to_skyflow_error(e):
    if isinstance(e, SkyflowError):
        return e
    if isinstance(e, (ApiError, ParsingError)):
        message, grpc_code, http_status, details = _parse_api_error_body(e.body)
        return SkyflowError(
            message=message,
            http_code=e.status_code,
            request_id=extract_request_id(e.headers),
            grpc_code=grpc_code,
            http_status=http_status,
            details=details,
        )
    return SkyflowError(
        message=str(e) if e else CommonMessages.Error.GENERIC_API_ERROR.value,
        http_code=None,
    )


def _parse_api_error_body(body):
    error = getattr(body, ERROR_BODY_KEY, None) if body is not None and not isinstance(body, dict) else None
    if error is not None and not isinstance(error, dict):
        return (
            getattr(error, ERROR_MESSAGE_KEY, None) or UNKNOWN_ERROR_MESSAGE,
            getattr(error, ERROR_GRPC_CODE_KEY, None),
            getattr(error, ERROR_HTTP_STATUS_KEY, None),
            getattr(error, ERROR_DETAILS_KEY, None) or [],
        )
    if isinstance(body, dict):
        error = body.get(ERROR_BODY_KEY)
        if isinstance(error, dict):
            return (
                error.get(ERROR_MESSAGE_KEY) or UNKNOWN_ERROR_MESSAGE,
                error.get(ERROR_GRPC_CODE_KEY, error.get(ERROR_GRPC_CODE_CAMEL_KEY)),
                error.get(ERROR_HTTP_STATUS_KEY, error.get(ERROR_HTTP_STATUS_CAMEL_KEY)),
                error.get(ERROR_DETAILS_KEY) or [],
            )
        if error is not None:
            return (str(error), None, None, [])
    return (UNKNOWN_ERROR_MESSAGE, None, None, [])
