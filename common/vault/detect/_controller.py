import base64
import json

from common.errors import SkyflowError
from common.utils import SkyflowMessages
from common.utils.constants import SKY_META_DATA_HEADER
from common.utils.logger import log_info, log_error_log

from . import _mappers as mappers
from ._constants import (
    ADDITIONAL_HEADERS_KEY,
    AUTHORIZATION_HEADER,
    BEARER_PREFIX,
    ENCODING_UTF_8,
    VAULT_ID_PARAM,
)
from ._errors import to_skyflow_error
from ._file_flow import complete_deidentify_file
from ._models import GetRunRequest
from ._validations import (
    validate_check_guardrails_request,
    validate_deidentify_file_request,
    validate_deidentify_string_request,
    validate_get_run_request,
    validate_reidentify_file_request,
    validate_reidentify_string_request,
)
from common.utils.enums.detect import DataSourceType

_DATA_SOURCE_BASE64 = DataSourceType.BASE64.value


class DetectController:
    def __init__(self, vault_client):
        self._vault_client = vault_client

    def deidentify_string(self, request):
        log_info(SkyflowMessages.Info.DEIDENTIFY_STRING_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_DEIDENTIFY_STRING_REQUEST.value, self._vault_client.get_logger())
        validate_deidentify_string_request(request)
        self._vault_client.initialize_client_configuration()
        kwargs = self.__omit_none(
            text=request.text,
            configuration_id=request.configuration_id,
            configuration=self.__configuration(request.configuration),
        )
        try:
            raw = self._vault_client.get_strings_v2_api().with_raw_response.deidentify_string_v2(
                request_options=self.__request_options(), **kwargs,
            )
            log_info(SkyflowMessages.Info.DEIDENTIFY_STRING_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            response = mappers.to_deidentify_string_response(raw.data)
            log_info(SkyflowMessages.Info.DEIDENTIFY_STRING_SUCCESS.value, self._vault_client.get_logger())
            return response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DEIDENTIFY_STRING_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

    def reidentify_string(self, request):
        log_info(SkyflowMessages.Info.REIDENTIFY_STRING_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_REIDENTIFY_STRING_REQUEST.value, self._vault_client.get_logger())
        validate_reidentify_string_request(request)
        self._vault_client.initialize_client_configuration()
        kwargs = self.__omit_none(
            redaction_level=self.__redaction_levels(request.redaction_level),
        )
        try:
            raw = self._vault_client.get_strings_v2_api().with_raw_response.reidentify_string_v2(
                vault_id=self._vault_client.get_vault_id(),
                text=request.text,
                request_options=self.__request_options(),
                **kwargs,
            )
            log_info(SkyflowMessages.Info.REIDENTIFY_STRING_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            response = mappers.to_reidentify_string_response(raw.data)
            log_info(SkyflowMessages.Info.REIDENTIFY_STRING_SUCCESS.value, self._vault_client.get_logger())
            return response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.REIDENTIFY_STRING_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

    def deidentify_file(self, request):
        log_info(SkyflowMessages.Info.DEIDENTIFY_FILE_V2_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_DEIDENTIFY_FILE_REQUEST.value, self._vault_client.get_logger())
        validate_deidentify_file_request(request)
        self._vault_client.initialize_client_configuration()
        data_source, value, data_format = self.__resolve_file_input(request)
        kwargs = self.__omit_none(
            data_format=data_format,
            configuration_id=request.configuration_id,
            configuration=self.__configuration(request.configuration),
        )
        try:
            raw = self._vault_client.get_files_v2_api().with_raw_response.deidentify_file_v2(
                data_source=data_source,
                value=value,
                request_options=self.__request_options(),
                **kwargs,
            )
            log_info(SkyflowMessages.Info.DEIDENTIFY_FILE_V2_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            run_id = raw.data.run_id
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DEIDENTIFY_FILE_V2_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

        response = complete_deidentify_file(
            request, run_id, self.__poll_fetcher, logger=self._vault_client.get_logger(),
        )
        log_info(SkyflowMessages.Info.DEIDENTIFY_FILE_V2_SUCCESS.value, self._vault_client.get_logger())
        return response

    def reidentify_file(self, request):
        log_info(SkyflowMessages.Info.REIDENTIFY_FILE_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_REIDENTIFY_FILE_REQUEST.value, self._vault_client.get_logger())
        validate_reidentify_file_request(request)
        self._vault_client.initialize_client_configuration()
        kwargs = self.__omit_none(
            data_format=request.data_format.value if request.data_format is not None else None,
            redaction_level=self.__redaction_levels(request.redaction_level),
        )
        try:
            raw = self._vault_client.get_files_v2_api().with_raw_response.reidentify_file_v2(
                data_source=request.data_source.value,
                value=request.value,
                vault_id=self._vault_client.get_vault_id(),
                request_options=self.__request_options(),
                **kwargs,
            )
            log_info(SkyflowMessages.Info.REIDENTIFY_FILE_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            response = mappers.to_reidentify_file_response(raw.data)
            log_info(SkyflowMessages.Info.REIDENTIFY_FILE_SUCCESS.value, self._vault_client.get_logger())
            return response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.REIDENTIFY_FILE_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

    def get_run(self, request):
        log_info(SkyflowMessages.Info.GET_RUN_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_GET_RUN_REQUEST.value, self._vault_client.get_logger())
        validate_get_run_request(request)
        self._vault_client.initialize_client_configuration()
        run_id = request.run_id.strip()
        try:
            raw = self._vault_client.get_files_v2_api().with_raw_response.get_run_v2(
                run_id,
                vault_id=self._vault_client.get_vault_id(),
                request_options=self.__request_options(),
            )
            log_info(SkyflowMessages.Info.GET_RUN_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            response = mappers.to_get_run_response(run_id, raw.data)
            log_info(SkyflowMessages.Info.GET_RUN_SUCCESS.value, self._vault_client.get_logger())
            return response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.GET_RUN_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

    def check_guardrails(self, request):
        log_info(SkyflowMessages.Info.CHECK_GUARDRAILS_TRIGGERED.value, self._vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATE_CHECK_GUARDRAILS_REQUEST.value, self._vault_client.get_logger())
        validate_check_guardrails_request(request)
        self._vault_client.initialize_client_configuration()
        kwargs = self.__omit_none(
            check_toxicity=request.check_toxicity,
            deny_topics=request.deny_topics,
        )
        try:
            raw = self._vault_client.get_guardrails_v2_api().with_raw_response.check_guardrails_v2(
                text=request.text,
                vault_id=self._vault_client.get_vault_id(),
                request_options=self.__request_options(),
                **kwargs,
            )
            log_info(SkyflowMessages.Info.CHECK_GUARDRAILS_REQUEST_RESOLVED.value, self._vault_client.get_logger())
            response = mappers.to_check_guardrails_response(raw.data)
            log_info(SkyflowMessages.Info.CHECK_GUARDRAILS_SUCCESS.value, self._vault_client.get_logger())
            return response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.CHECK_GUARDRAILS_REQUEST_REJECTED.value, self._vault_client.get_logger())
            raise to_skyflow_error(e)

    def __poll_fetcher(self, run_id):
        return self.get_run(GetRunRequest(run_id=run_id))

    def __configuration(self, configuration):
        if configuration is None:
            return None
        return mappers.to_detect_config(configuration, self._vault_client.get_vault_id())

    def __redaction_levels(self, redaction_level):
        if redaction_level is None:
            return None
        return mappers.to_redaction_levels(redaction_level)

    def __resolve_file_input(self, request):
        if request.file_path is not None or request.file is not None:
            content, name = self.__read_file(request)
            value = base64.b64encode(content).decode(ENCODING_UTF_8)
            data_source = _DATA_SOURCE_BASE64
            data_format = request.data_format if request.data_format is not None else mappers.infer_format(name)
            return data_source, value, data_format.value if data_format is not None else None
        data_source = request.data_source.value if request.data_source is not None else None
        data_format = request.data_format.value if request.data_format is not None else None
        return data_source, request.value, data_format

    def __read_file(self, request):
        try:
            if request.file_path is not None:
                with open(request.file_path, "rb") as handle:
                    return handle.read(), request.file_path
            return request.file.read(), getattr(request.file, "name", None)
        except (OSError, ValueError):
            raise SkyflowError(
                SkyflowMessages.Error.FAILED_TO_ENCODE_FILE.value,
                SkyflowMessages.ErrorCodes.INVALID_INPUT.value,
            )

    def __headers(self):
        headers = {SKY_META_DATA_HEADER: json.dumps(self._vault_client.get_sdk_metrics())}
        token = self._vault_client.get_current_bearer_token()
        if token:
            headers[AUTHORIZATION_HEADER] = BEARER_PREFIX + token
        return headers

    def __request_options(self):
        return {ADDITIONAL_HEADERS_KEY: self.__headers()}

    def __omit_none(self, **kwargs):
        return {key: value for key, value in kwargs.items() if value is not None}
