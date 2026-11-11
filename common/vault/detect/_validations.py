import os

from common.errors import SkyflowError
from common.utils import SkyflowMessages

from ._constants import (
    MIN_WAIT_TIME_SECONDS,
    MAX_WAIT_TIME_SECONDS,
    MIN_MAX_ATTEMPTS,
    MAX_MAX_ATTEMPTS,
)

_INVALID_INPUT = SkyflowMessages.ErrorCodes.INVALID_INPUT.value


def _is_blank(value):
    return value is None or not str(value).strip()


def _invalid(message):
    return SkyflowError(message, _INVALID_INPUT)


def validate_deidentify_string_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.DEIDENTIFY_STRING_REQUEST_NULL.value)
    if _is_blank(request.text):
        raise _invalid(SkyflowMessages.Error.INVALID_TEXT_IN_DEIDENTIFY_STRING.value)


def validate_deidentify_file_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.DEIDENTIFY_FILE_REQUEST_NULL.value)
    sources = sum(
        1 for source in (request.file_path, request.file, request.value) if source is not None
    )
    if sources == 0:
        raise _invalid(SkyflowMessages.Error.MISSING_FILE_SOURCE_IN_DEIDENTIFY_FILE.value)
    if sources > 1:
        raise _invalid(SkyflowMessages.Error.MULTIPLE_FILE_SOURCES_IN_DEIDENTIFY_FILE.value)
    if request.value is not None:
        if request.data_source is None:
            raise _invalid(SkyflowMessages.Error.INVALID_DATA_SOURCE_IN_DEIDENTIFY_FILE.value)
        if _is_blank(request.value):
            raise _invalid(SkyflowMessages.Error.INVALID_VALUE_IN_DEIDENTIFY_FILE.value)
    elif request.file_path is not None and not os.path.isfile(request.file_path):
        raise _invalid(SkyflowMessages.Error.FILE_NOT_FOUND_TO_DEIDENTIFY.value)
    validate_poll_options(request.poll_options)
    if request.poll_options is None and not _is_blank(request.output_directory):
        raise _invalid(SkyflowMessages.Error.OUTPUT_DIRECTORY_WITHOUT_POLL_OPTIONS.value)


def validate_poll_options(poll_options):
    if poll_options is None:
        return
    wait_time = poll_options.wait_time
    if wait_time is not None and (wait_time < MIN_WAIT_TIME_SECONDS or wait_time > MAX_WAIT_TIME_SECONDS):
        raise _invalid(SkyflowMessages.Error.INVALID_WAIT_TIME_IN_POLL_OPTIONS.value)
    max_attempts = poll_options.max_attempts
    if max_attempts is not None and (max_attempts < MIN_MAX_ATTEMPTS or max_attempts > MAX_MAX_ATTEMPTS):
        raise _invalid(SkyflowMessages.Error.INVALID_MAX_ATTEMPTS_IN_POLL_OPTIONS.value)


def validate_reidentify_string_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.REIDENTIFY_STRING_REQUEST_NULL.value)
    if _is_blank(request.text):
        raise _invalid(SkyflowMessages.Error.INVALID_TEXT_IN_REIDENTIFY_STRING.value)


def validate_get_run_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.GET_RUN_REQUEST_NULL.value)
    if _is_blank(request.run_id):
        raise _invalid(SkyflowMessages.Error.INVALID_RUN_ID_IN_GET_RUN.value)


def validate_check_guardrails_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.CHECK_GUARDRAILS_REQUEST_NULL.value)
    if _is_blank(request.text):
        raise _invalid(SkyflowMessages.Error.INVALID_TEXT_IN_CHECK_GUARDRAILS.value)


def validate_reidentify_file_request(request):
    if request is None:
        raise _invalid(SkyflowMessages.Error.REIDENTIFY_FILE_REQUEST_NULL.value)
    if request.data_source is None:
        raise _invalid(SkyflowMessages.Error.INVALID_DATA_SOURCE_IN_REIDENTIFY_FILE.value)
    if _is_blank(request.value):
        raise _invalid(SkyflowMessages.Error.INVALID_VALUE_IN_REIDENTIFY_FILE.value)
