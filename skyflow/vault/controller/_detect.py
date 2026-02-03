import io
import json
import os
import base64
import time
from skyflow.generated.rest import FileDataDeidentifyText, FileDataDeidentifyPdf, FileDataDeidentifyPresentation, \
    FileDataDeidentifySpreadsheet, FileDataDeidentifyDocument, FileDataDeidentifyStructuredText, FileData, \
    FileDataDeidentifyImage, Format, FileDataDeidentifyAudio, WordCharacterCount, DetectRunsResponse
from skyflow.utils._skyflow_messages import SkyflowMessages
from skyflow.utils._utils import get_attribute, get_metrics, handle_exception, parse_deidentify_text_response, parse_reidentify_text_response
from skyflow.utils.constants import (SKY_META_DATA_HEADER, DetectStatus, FileExtension, 
                                      FileProcessing, EncodingType, DeidentifyField, DeidentifyFileRequestField, FileUploadField, OptionField)
from skyflow.utils.logger import log_info, log_error_log
from skyflow.utils.validations import validate_deidentify_file_request, validate_get_detect_run_request
from skyflow.utils.validations._validations import validate_deidentify_text_request, validate_reidentify_text_request
from typing import Dict, Any
from skyflow.vault.detect import DeidentifyTextRequest, DeidentifyTextResponse, ReidentifyTextRequest, \
    ReidentifyTextResponse, DeidentifyFileRequest, DeidentifyFileResponse, GetDetectRunRequest

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
        
        deidentify_text_body[DeidentifyField.TEXT] = request.text
        deidentify_text_body[DeidentifyField.ENTITY_TYPES] = parsed_entity_types
        deidentify_text_body[DeidentifyField.TOKEN_TYPE] = self.__get_token_format(request)
        deidentify_text_body[DeidentifyField.ALLOW_REGEX] = request.allow_regex_list
        deidentify_text_body[DeidentifyField.RESTRICT_REGEX] = request.restrict_regex_list 
        deidentify_text_body[DeidentifyField.TRANSFORMATIONS] = self.__get_transformations(request)
        
        return deidentify_text_body

    def ___build_reidentify_text_body(self, request: ReidentifyTextRequest) -> Dict[str, Any]:
        parsed_format = Format(
            redacted=request.redacted_entities,
            masked=request.masked_entities,
            plaintext=request.plain_text_entities
        )
        reidentify_text_body = {}
        reidentify_text_body[DeidentifyField.TEXT] = request.text
        reidentify_text_body[DeidentifyField.FORMAT] = parsed_format
        return reidentify_text_body

    def _get_file_extension(self, filename: str):
        return filename.split('.')[-1].lower() if '.' in filename else ''

    def __poll_for_processed_file(self, run_id, max_wait_time=64):
        max_wait_time = 64 if max_wait_time is None else max_wait_time
        files_api = self.__vault_client.get_detect_file_api().with_raw_response
        current_wait_time = 1  # Start with 1 second
        try:
            while True:
                response = files_api.get_run(run_id, vault_id=self.__vault_client.get_vault_id(), request_options=self.__get_headers()).data
                status = response.status
                if status == DetectStatus.IN_PROGRESS:
                    if current_wait_time >= max_wait_time:
                        return DeidentifyFileResponse(run_id=run_id, status=DetectStatus.IN_PROGRESS)
                    else:
                        next_wait_time = current_wait_time * 2
                        if next_wait_time >= max_wait_time:
                            wait_time = max_wait_time - current_wait_time
                            current_wait_time = max_wait_time
                        else:
                            wait_time = next_wait_time
                            current_wait_time = next_wait_time
                        time.sleep(wait_time)
                elif status == DetectStatus.SUCCESS or status == DetectStatus.FAILED:
                    return response
        except Exception as e:
            raise e

    def __save_deidentify_file_response_output(self, response: DetectRunsResponse, output_directory: str, original_file_name: str, name_without_ext: str):
        if not response or not hasattr(response, DeidentifyField.OUTPUT) or not response.output or not output_directory:
            return

        if not os.path.exists(output_directory):
            return

        deidentify_file_prefix = FileProcessing.PROCESSED_PREFIX
        output_list = response.output

        base_original_filename = os.path.basename(original_file_name)
        base_name_without_ext = os.path.splitext(base_original_filename)[0]

        for idx, output in enumerate(output_list):
            try:
                processed_file = get_attribute(output, DeidentifyField.PROCESSED_FILE_RESPONSE_KEY, DeidentifyField.PROCESSED_FILE)
                processed_file_type = get_attribute(output, DeidentifyField.PROCESSED_FILE_TYPE_RESPONSE_KEY, DeidentifyField.PROCESSED_FILE_TYPE)
                processed_file_extension = get_attribute(output, DeidentifyField.PROCESSED_FILE_EXTENSION_RESPONSE_KEY, DeidentifyField.PROCESSED_FILE_EXTENSION)

                if not processed_file:
                    continue

                decoded_data = base64.b64decode(processed_file)
                
                if idx == 0 or processed_file_type == DeidentifyField.REDACTED_FILE:
                    output_file_name = os.path.join(output_directory, deidentify_file_prefix + base_original_filename)
                    if processed_file_extension:
                        output_file_name = os.path.join(output_directory, f"{deidentify_file_prefix}{base_name_without_ext}.{processed_file_extension}")
                else:
                    output_file_name = os.path.join(output_directory, f"{deidentify_file_prefix}{base_name_without_ext}.{processed_file_extension}")
                
                with open(output_file_name, 'wb') as f:
                    f.write(decoded_data)
            except Exception as e:
                log_error_log(SkyflowMessages.ErrorLogs.SAVING_DEIDENTIFY_FILE_FAILED.value, self.__vault_client.get_logger())
                handle_exception(e, self.__vault_client.get_logger())

    def __parse_deidentify_file_response(self, data, run_id=None, status=None):
        output = getattr(data, DeidentifyField.OUTPUT, [])
        status_val = getattr(data, DeidentifyField.STATUS, None) or status
        run_id_val = getattr(data, DeidentifyField.RUN_ID, None) or run_id

        word_count = None
        char_count = None

        word_character_count = getattr(data, DeidentifyField.WORD_CHARACTER_COUNT, None)
        if word_character_count and isinstance(word_character_count, WordCharacterCount):
            word_count = getattr(word_character_count, DeidentifyField.WORD_COUNT, None)
            char_count = getattr(word_character_count, DeidentifyField.CHARACTER_COUNT, None)

        size = getattr(data, DeidentifyField.SIZE, None)

        size = float(size) if size is not None else None

        duration = getattr(data, DeidentifyField.DURATION, None)
        pages = getattr(data, DeidentifyField.PAGES, None)
        slides = getattr(data, DeidentifyField.SLIDES, None)

        def output_to_dict_list(output):
            result = []
            for o in output:
                if isinstance(o, dict):
                    result.append({
                        DeidentifyField.FILE: o.get(DeidentifyField.PROCESSED_FILE),
                        DeidentifyField.TYPE: o.get(DeidentifyField.PROCESSED_FILE_TYPE),
                        DeidentifyField.EXTENSION: o.get(DeidentifyField.PROCESSED_FILE_EXTENSION)
                    })
                else:
                    result.append({
                        DeidentifyField.FILE: getattr(o, DeidentifyField.PROCESSED_FILE, None),
                        DeidentifyField.TYPE: getattr(o, DeidentifyField.PROCESSED_FILE_TYPE, None),
                        DeidentifyField.EXTENSION: getattr(o, DeidentifyField.PROCESSED_FILE_EXTENSION, None)
                    })
            return result

        output_list = output_to_dict_list(output)
        first_output = output_list[0] if output_list else {}

        entities = [o for o in output_list if o.get(DeidentifyField.TYPE) == FileProcessing.ENTITIES]

        base64_string = first_output.get(DeidentifyField.FILE, None)
        extension = first_output.get(DeidentifyField.EXTENSION, None)

        if base64_string is not None:
                file_bytes = base64.b64decode(base64_string)
                file_obj = io.BytesIO(file_bytes)
                file_obj.name = f"{FileProcessing.DEIDENTIFIED_PREFIX}{extension}" if extension else DeidentifyField.PROCESSED_FILE
        else:
            file_obj = None
    
        return DeidentifyFileResponse(
            file_base64=base64_string,
            file=file_obj,
            type=first_output.get(DeidentifyField.TYPE, DetectStatus.UNKNOWN),
            extension=extension,
            word_count=word_count,
            char_count=char_count,
            size_in_kb=size,
            duration_in_seconds=duration,
            page_count=pages,
            slide_count=slides,
            entities=entities,
            run_id=run_id_val,
            status=status_val,
        )

    def __get_token_format(self, request):
        if not hasattr(request, DeidentifyField.TOKEN_FORMAT) or request.token_format is None:
            return None
        return {
            DeidentifyField.DEFAULT: getattr(request.token_format, DeidentifyField.DEFAULT, None),
            DeidentifyField.ENTITY_UNQ_COUNTER: getattr(request.token_format, DeidentifyField.ENTITY_UNIQUE_COUNTER, None),
            DeidentifyField.ENTITY_ONLY: getattr(request.token_format, DeidentifyField.ENTITY_ONLY, None),
        }

    def __get_transformations(self, request):
        if not hasattr(request, DeidentifyField.TRANSFORMATIONS) or request.transformations is None:
            return None
        shift_dates = getattr(request.transformations, DeidentifyField.SHIFT_DATES, None)
        if shift_dates is None:
            return None
        return {
            DeidentifyField.SHIFT_DATES: {
                DeidentifyField.MAX_DAYS: getattr(shift_dates, DeidentifyField.MAX, None),
                DeidentifyField.MIN_DAYS: getattr(shift_dates, DeidentifyField.MIN, None),
                DeidentifyField.ENTITY_TYPES: getattr(shift_dates, DeidentifyField.ENTITIES, None)
            }
        }

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
              text=deidentify_text_body[DeidentifyField.TEXT],
              entity_types=deidentify_text_body[DeidentifyField.ENTITY_TYPES],
              allow_regex=deidentify_text_body[DeidentifyField.ALLOW_REGEX],
              restrict_regex=deidentify_text_body[DeidentifyField.RESTRICT_REGEX],
              token_type=deidentify_text_body[DeidentifyField.TOKEN_TYPE],
              transformations=deidentify_text_body[DeidentifyField.TRANSFORMATIONS],
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
                text=reidentify_text_body[DeidentifyField.TEXT],
                format=reidentify_text_body[DeidentifyField.FORMAT],
                request_options=self.__get_headers()
            )
            reidentify_text_response = parse_reidentify_text_response(api_response)
            log_info(SkyflowMessages.Info.REIDENTIFY_TEXT_SUCCESS.value, self.__vault_client.get_logger())
            return reidentify_text_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.REIDENTIFY_TEXT_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def __get_file_from_request(self, request: DeidentifyFileRequest):
        file_input = request.file
        
        # Check for file
        if hasattr(file_input, FileUploadField.FILE) and file_input.file is not None:
            return file_input.file
            
        # Check for file_path if file is not provided
        if hasattr(file_input, FileUploadField.FILE_PATH) and file_input.file_path is not None:
                return open(file_input.file_path, 'rb')

    def deidentify_file(self, request: DeidentifyFileRequest):
        log_info(SkyflowMessages.Info.DETECT_FILE_TRIGGERED.value, self.__vault_client.get_logger())
        validate_deidentify_file_request(self.__vault_client.get_logger(), request)
        self.__initialize()
        files_api = self.__vault_client.get_detect_file_api().with_raw_response
        file_obj = self.__get_file_from_request(request)
        file_name = getattr(file_obj, FileUploadField.NAME, None)
        file_extension = self._get_file_extension(file_name) if file_name else None
        file_content = file_obj.read()
        base64_string = base64.b64encode(file_content).decode(EncodingType.UTF_8)

        try:
            if file_extension == FileExtension.TXT:
                req_file = FileDataDeidentifyText(base_64=base64_string, data_format=FileExtension.TXT)
                api_call = files_api.deidentify_text
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.TRANSFORMATIONS: self.__get_transformations(request),
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.MP3, FileExtension.WAV]:
                req_file = FileDataDeidentifyAudio(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_audio
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.TRANSFORMATIONS: self.__get_transformations(request),
                    DeidentifyFileRequestField.OUTPUT_TRANSCRIPTION: getattr(request, DeidentifyFileRequestField.OUTPUT_TRANSCRIPTION, None),
                    DeidentifyFileRequestField.OUTPUT_PROCESSED_AUDIO: getattr(request, DeidentifyFileRequestField.OUTPUT_PROCESSED_AUDIO, None),
                    DeidentifyField.BLEEP_GAIN: getattr(request, DeidentifyFileRequestField.BLEEP, None).gain if getattr(request, DeidentifyFileRequestField.BLEEP, None) is not None else None,
                    DeidentifyField.BLEEP_FREQUENCY: getattr(request, DeidentifyFileRequestField.BLEEP, None).frequency if getattr(request, DeidentifyFileRequestField.BLEEP, None) is not None else None,
                    DeidentifyField.BLEEP_START_PADDING: getattr(request, DeidentifyFileRequestField.BLEEP, None).start_padding if getattr(request, DeidentifyFileRequestField.BLEEP, None) is not None else None,
                    DeidentifyField.BLEEP_STOP_PADDING: getattr(request, DeidentifyFileRequestField.BLEEP, None).stop_padding if getattr(request, DeidentifyFileRequestField.BLEEP, None) is not None else None,
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension == FileExtension.PDF:
                req_file = FileDataDeidentifyPdf(base_64=base64_string)
                api_call = files_api.deidentify_pdf
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyFileRequestField.MAX_RESOLUTION: getattr(request, DeidentifyFileRequestField.MAX_RESOLUTION, None),
                    DeidentifyFileRequestField.PIXEL_DENSITY: getattr(request, DeidentifyFileRequestField.PIXEL_DENSITY, None),
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.JPEG, FileExtension.JPG, FileExtension.PNG, FileExtension.BMP, FileExtension.TIF, FileExtension.TIFF]:
                req_file = FileDataDeidentifyImage(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_image
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyFileRequestField.MASKING_METHOD: getattr(request, DeidentifyFileRequestField.MASKING_METHOD, None),
                    DeidentifyFileRequestField.OUTPUT_OCR_TEXT: getattr(request, DeidentifyFileRequestField.OUTPUT_OCR_TEXT, None),
                    DeidentifyFileRequestField.OUTPUT_PROCESSED_IMAGE: getattr(request, DeidentifyFileRequestField.OUTPUT_PROCESSED_IMAGE, None),
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.PPT, FileExtension.PPTX]:
                req_file = FileDataDeidentifyPresentation(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_presentation
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.CSV, FileExtension.XLS, FileExtension.XLSX]:
                req_file = FileDataDeidentifySpreadsheet(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_spreadsheet
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.DOC, FileExtension.DOCX]:
                req_file = FileDataDeidentifyDocument(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_document
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            elif file_extension in [FileExtension.JSON, FileExtension.XML]:
                req_file = FileDataDeidentifyStructuredText(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_structured_text
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.TRANSFORMATIONS: self.__get_transformations(request),
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            else:
                req_file = FileData(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_file
                api_kwargs = {
                    OptionField.VAULT_ID: self.__vault_client.get_vault_id(),
                    DeidentifyField.FILE: req_file,
                    DeidentifyField.ENTITY_TYPES: request.entities,
                    DeidentifyField.TOKEN_TYPE: self.__get_token_format(request),
                    DeidentifyField.ALLOW_REGEX: request.allow_regex_list,
                    DeidentifyField.RESTRICT_REGEX: request.restrict_regex_list,
                    DeidentifyField.TRANSFORMATIONS: self.__get_transformations(request),
                    DeidentifyField.REQUEST_OPTIONS: self.__get_headers()
                }

            log_info(SkyflowMessages.Info.DETECT_FILE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
            api_response = api_call(**api_kwargs)

            run_id = getattr(api_response.data, DeidentifyField.RUN_ID, None)

            processed_response = self.__poll_for_processed_file(run_id, request.wait_time)
            if request.output_directory and processed_response.status == DetectStatus.SUCCESS:
                name_without_ext, _ = os.path.splitext(file_name)
                self.__save_deidentify_file_response_output(processed_response, request.output_directory, file_name, name_without_ext)

            parsed_response = self.__parse_deidentify_file_response(processed_response, run_id)
            log_info(SkyflowMessages.Info.DETECT_FILE_SUCCESS.value, self.__vault_client.get_logger())
            return parsed_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETECT_FILE_REQUEST_REJECTED.value,
                          self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

    def get_detect_run(self, request: GetDetectRunRequest):
        log_info(SkyflowMessages.Info.GET_DETECT_RUN_TRIGGERED.value,self.__vault_client.get_logger())
        log_info(SkyflowMessages.Info.VALIDATING_GET_DETECT_RUN_INPUT.value, self.__vault_client.get_logger())
        validate_get_detect_run_request(self.__vault_client.get_logger(), request)
        self.__initialize()

        files_api = self.__vault_client.get_detect_file_api().with_raw_response
        run_id = request.run_id
        try:
            response = files_api.get_run(
                run_id,
                vault_id=self.__vault_client.get_vault_id(),
                request_options=self.__get_headers()
            )
            if response.data.status == DetectStatus.IN_PROGRESS:
                parsed_response = self.__parse_deidentify_file_response(DeidentifyFileResponse(run_id=run_id, status=DetectStatus.IN_PROGRESS))
            else:
                parsed_response = self.__parse_deidentify_file_response(response.data, run_id, response.data.status)
            log_info(SkyflowMessages.Info.GET_DETECT_RUN_SUCCESS.value,self.__vault_client.get_logger())
            return parsed_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETECT_FILE_REQUEST_REJECTED.value,
                          self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

