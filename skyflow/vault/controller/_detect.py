import json
from skyflow.generated.rest.types.token_type import TokenType
from skyflow.generated.rest.types.transformations import Transformations
from skyflow.generated.rest.types.transformations_shift_dates import TransformationsShiftDates
from skyflow.utils._skyflow_messages import SkyflowMessages
from skyflow.utils._utils import get_metrics, handle_exception, parse_deidentify_text_response, parse_reidentify_text_response
from skyflow.utils.constants import SKY_META_DATA_HEADER
from skyflow.utils.logger import log_info, log_error_log
from skyflow.utils.validations._validations import validate_deidentify_text_request, validate_reidentify_text_request
from typing import Dict, Any
from skyflow.generated.rest.strings.types.reidentify_string_request_format import ReidentifyStringRequestFormat
from skyflow.vault.detect import DeidentifyTextRequest, DeidentifyTextResponse, ReidentifyTextRequest, ReidentifyTextResponse

class Detect:
    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def __initialize(self):
        self.__vault_client.initialize_client_configuration()

    def __get_headers(self):
        headers = {
            SKY_META_DATA_HEADER: json.dumps(get_metrics())
        }
        return headers
      
    def ___build_deidentify_text_body(self, request: DeidentifyTextRequest) -> Dict[str, Any]:
        deidentify_text_body = {}
        parsed_entity_types = request.entities

        parsed_token_type = None
        if request.token_format is not None:
            parsed_token_type = TokenType(
                default = request.token_format.default,
                vault_token = request.token_format.vault_token,
                entity_unq_counter = request.token_format.entity_unique_counter,
                entity_only = request.token_format.entity_only
            )
        parsed_transformations = None
        if request.transformations is not None:
            parsed_transformations = Transformations(
                shift_dates = TransformationsShiftDates(
                    max_days = request.transformations.shift_dates.max,
                    min_days = request.transformations.shift_dates.min,
                    entity_types = request.transformations.shift_dates.entities
                )
            )
        
        deidentify_text_body['text'] = request.text
        deidentify_text_body['entity_types'] = parsed_entity_types
        deidentify_text_body['token_type'] = parsed_token_type
        deidentify_text_body['allow_regex'] = request.allow_regex_list
        deidentify_text_body['restrict_regex'] = request.restrict_regex_list 
        deidentify_text_body['transformations'] = parsed_transformations 
        
        return deidentify_text_body

    def ___build_reidentify_text_body(self, request: ReidentifyTextRequest) -> Dict[str, Any]:
        parsed_format = ReidentifyStringRequestFormat(
            redacted=request.redacted_entities,
            masked=request.masked_entities,
            plaintext=request.plain_text_entities
        )
        reidentify_text_body = {}
        reidentify_text_body['text'] = request.text
        reidentify_text_body['format'] = parsed_format
        return reidentify_text_body

    def deidentify_text(self, request: DeidentifyTextRequest) -> DeidentifyTextResponse:
        log_info(SkyflowMessages.Info.VALIDATING_DEIDENTIFY_TEXT_INPUT.value, self.__vault_client.get_logger())
        validate_deidentify_text_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.DEIDENTIFY_TEXT_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        detect_api = self.__vault_client.get_detect_text_api()
        deidentify_text_body = self.___build_deidentify_text_body(request)
        
        try:
            log_info(SkyflowMessages.Info.DEIDENTIFY_TEXT_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = detect_api.deidentify_string(
              vault_id=self.__vault_client.get_vault_id(),
              text=deidentify_text_body['text'],
              entity_types=deidentify_text_body['entity_types'],
              allow_regex=deidentify_text_body['allow_regex'],
              restrict_regex=deidentify_text_body['restrict_regex'],
              token_type=deidentify_text_body['token_type'],
              transformations=deidentify_text_body['transformations'],
              request_options=self.__get_headers()
            )
            deidentify_text_response = parse_deidentify_text_response(api_response)
            log_info(SkyflowMessages.Info.DEIDENTIFY_TEXT_SUCCESS.value, self.__vault_client.get_logger())
            return deidentify_text_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DEIDENTIFY_TEXT_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def reidentify_text(self, request: ReidentifyTextRequest) -> ReidentifyTextResponse:
        log_info(SkyflowMessages.Info.VALIDATING_REIDENTIFY_TEXT_INPUT.value, self.__vault_client.get_logger())
        validate_reidentify_text_request(self.__vault_client.get_logger(), request)
        log_info(SkyflowMessages.Info.REIDENTIFY_TEXT_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
        self.__initialize()
        detect_api = self.__vault_client.get_detect_text_api()
        reidentify_text_body = self.___build_reidentify_text_body(request)
        
        try:
            log_info(SkyflowMessages.Info.REIDENTIFY_TEXT_TRIGGERED.value, self.__vault_client.get_logger())
            api_response = detect_api.reidentify_string(
                vault_id=self.__vault_client.get_vault_id(),
                text=reidentify_text_body['text'],
                format=reidentify_text_body['format'],
                request_options=self.__get_headers()
            )
            reidentify_text_response = parse_reidentify_text_response(api_response)
            log_info(SkyflowMessages.Info.REIDENTIFY_TEXT_SUCCESS.value, self.__vault_client.get_logger())
            return reidentify_text_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.REIDENTIFY_TEXT_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())
