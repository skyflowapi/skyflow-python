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
from skyflow.utils.constants import SKY_META_DATA_HEADER
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
        
        deidentify_text_body['text'] = request.text
        deidentify_text_body['entity_types'] = parsed_entity_types
        deidentify_text_body['token_type'] = self.__get_token_format(request)
        deidentify_text_body['allow_regex'] = request.allow_regex_list
        deidentify_text_body['restrict_regex'] = request.restrict_regex_list 
        deidentify_text_body['transformations'] = self.__get_transformations(request)
        
        return deidentify_text_body

    def ___build_reidentify_text_body(self, request: ReidentifyTextRequest) -> Dict[str, Any]:
        parsed_format = Format(
            redacted=request.redacted_entities,
            masked=request.masked_entities,
            plaintext=request.plain_text_entities
        )
        reidentify_text_body = {}
        reidentify_text_body['text'] = request.text
        reidentify_text_body['format'] = parsed_format
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
                if status == 'IN_PROGRESS':
                    if current_wait_time >= max_wait_time:
                        return DeidentifyFileResponse(run_id=run_id, status='IN_PROGRESS')
                    else:
                        next_wait_time = current_wait_time * 2
                        if next_wait_time >= max_wait_time:
                            wait_time = max_wait_time - current_wait_time
                            current_wait_time = max_wait_time
                        else:
                            wait_time = next_wait_time
                            current_wait_time = next_wait_time
                        time.sleep(wait_time)
                elif status == 'SUCCESS' or status == 'FAILED':
                    return response
        except Exception as e:
            raise e

    def __save_deidentify_file_response_output(self, response: DetectRunsResponse, output_directory: str, original_file_name: str, name_without_ext: str):
        if not response or not hasattr(response, 'output') or not response.output or not output_directory:
            return

        if not os.path.exists(output_directory):
            return

        deidentify_file_prefix = "processed-"
        output_list = response.output

        base_original_filename = os.path.basename(original_file_name)
        base_name_without_ext = os.path.splitext(base_original_filename)[0]

        for idx, output in enumerate(output_list):
            try:
                processed_file = get_attribute(output, 'processedFile', 'processed_file')
                processed_file_type = get_attribute(output, 'processedFileType', 'processed_file_type')
                processed_file_extension = get_attribute(output, 'processedFileExtension', 'processed_file_extension')

                if not processed_file:
                    continue

                decoded_data = base64.b64decode(processed_file)
                
                if idx == 0 or processed_file_type == 'redacted_file':
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
        output = getattr(data, "output", [])
        status_val = getattr(data, "status", None) or status
        run_id_val = getattr(data, "run_id", None) or run_id

        word_count = None
        char_count = None

        word_character_count = getattr(data, "word_character_count", None)
        if word_character_count and isinstance(word_character_count, WordCharacterCount):
            word_count = word_character_count.word_count
            char_count = word_character_count.character_count

        size = getattr(data, "size", None)

        size = float(size) if size is not None else None

        duration = getattr(data, "duration", None)
        pages = getattr(data, "pages", None)
        slides = getattr(data, "slides", None)

        def output_to_dict_list(output):
            result = []
            for o in output:
                if isinstance(o, dict):
                    result.append({
                        "file": o.get("processed_file"),
                        "type": o.get("processed_file_type"),
                        "extension": o.get("processed_file_extension")
                    })
                else:
                    result.append({
                        "file": getattr(o, "processed_file", None),
                        "type": getattr(o, "processed_file_type", None),
                        "extension": getattr(o, "processed_file_extension", None)
                    })
            return result

        output_list = output_to_dict_list(output)
        first_output = output_list[0] if output_list else {}

        entities = [o for o in output_list if o.get("type") == "entities"]

        base64_string = first_output.get("file", None)
        extension = first_output.get("extension", None)

        if base64_string is not None:
                file_bytes = base64.b64decode(base64_string)
                file_obj = io.BytesIO(file_bytes)
                file_obj.name = f"deidentified.{extension}" if extension else "processed_file"
        else:
            file_obj = None
    
        return DeidentifyFileResponse(
            file_base64=base64_string,
            file=file_obj,
            type=first_output.get("type", "UNKNOWN"),
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
        if not hasattr(request, "token_format") or request.token_format is None:
            return None
        return {
            'default': getattr(request.token_format, "default", None),
            'entity_unq_counter': getattr(request.token_format, "entity_unique_counter", None),
            'entity_only': getattr(request.token_format, "entity_only", None),
        }

    def __get_transformations(self, request):
        if not hasattr(request, "transformations") or request.transformations is None:
            return None
        shift_dates = getattr(request.transformations, "shift_dates", None)
        if shift_dates is None:
            return None
        return {
            'shift_dates': {
                'max_days': getattr(shift_dates, "max", None),
                'min_days': getattr(shift_dates, "min", None),
                'entity_types': getattr(shift_dates, "entities", None)
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

    def __get_file_from_request(self, request: DeidentifyFileRequest):
        file_input = request.file
        
        # Check for file
        if hasattr(file_input, 'file') and file_input.file is not None:
            return file_input.file
            
        # Check for file_path if file is not provided
        if hasattr(file_input, 'file_path') and file_input.file_path is not None:
                return open(file_input.file_path, 'rb')

    def deidentify_file(self, request: DeidentifyFileRequest):
        log_info(SkyflowMessages.Info.DETECT_FILE_TRIGGERED.value, self.__vault_client.get_logger())
        validate_deidentify_file_request(self.__vault_client.get_logger(), request)
        self.__initialize()
        files_api = self.__vault_client.get_detect_file_api().with_raw_response
        file_obj = self.__get_file_from_request(request)
        file_name = getattr(file_obj, 'name', None)
        file_extension = self._get_file_extension(file_name) if file_name else None
        file_content = file_obj.read()
        base64_string = base64.b64encode(file_content).decode('utf-8')

        try:
            if file_extension == 'txt':
                req_file = FileDataDeidentifyText(base_64=base64_string, data_format="txt")
                api_call = files_api.deidentify_text
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'transformations': self.__get_transformations(request),
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['mp3', 'wav']:
                req_file = FileDataDeidentifyAudio(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_audio
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'transformations': self.__get_transformations(request),
                    'output_transcription': getattr(request, 'output_transcription', None),
                    'output_processed_audio': getattr(request, 'output_processed_audio', None),
                    'bleep_gain': getattr(request, 'bleep', None).gain if getattr(request, 'bleep', None) is not None else None,
                    'bleep_frequency': getattr(request, 'bleep', None).frequency if getattr(request, 'bleep', None) is not None else None,
                    'bleep_start_padding': getattr(request, 'bleep', None).start_padding if getattr(request, 'bleep', None) is not None else None,
                    'bleep_stop_padding': getattr(request, 'bleep', None).stop_padding if getattr(request, 'bleep', None) is not None else None,
                    'request_options': self.__get_headers()
                }

            elif file_extension == 'pdf':
                req_file = FileDataDeidentifyPdf(base_64=base64_string)
                api_call = files_api.deidentify_pdf
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'max_resolution': getattr(request, 'max_resolution', None),
                    'density': getattr(request, 'pixel_density', None),
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['jpeg', 'jpg', 'png', 'bmp', 'tif', 'tiff']:
                req_file = FileDataDeidentifyImage(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_image
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'masking_method': getattr(request, 'masking_method', None),
                    'output_ocr_text': getattr(request, 'output_ocr_text', None),
                    'output_processed_image': getattr(request, 'output_processed_image', None),
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['ppt', 'pptx']:
                req_file = FileDataDeidentifyPresentation(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_presentation
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['csv', 'xls', 'xlsx']:
                req_file = FileDataDeidentifySpreadsheet(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_spreadsheet
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['doc', 'docx']:
                req_file = FileDataDeidentifyDocument(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_document
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'request_options': self.__get_headers()
                }

            elif file_extension in ['json', 'xml']:
                req_file = FileDataDeidentifyStructuredText(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_structured_text
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'transformations': self.__get_transformations(request),
                    'request_options': self.__get_headers()
                }

            else:
                req_file = FileData(base_64=base64_string, data_format=file_extension)
                api_call = files_api.deidentify_file
                api_kwargs = {
                    'vault_id': self.__vault_client.get_vault_id(),
                    'file': req_file,
                    'entity_types': request.entities,
                    'token_type': self.__get_token_format(request),
                    'allow_regex': request.allow_regex_list,
                    'restrict_regex': request.restrict_regex_list,
                    'transformations': self.__get_transformations(request),
                    'request_options': self.__get_headers()
                }

            log_info(SkyflowMessages.Info.DETECT_FILE_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
            api_response = api_call(**api_kwargs)

            run_id = getattr(api_response.data, 'run_id', None)

            processed_response = self.__poll_for_processed_file(run_id, request.wait_time)
            if request.output_directory and processed_response.status == 'SUCCESS':
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
            if response.data.status == 'IN_PROGRESS':
                parsed_response = self.__parse_deidentify_file_response(DeidentifyFileResponse(run_id=run_id, status='IN_PROGRESS'))
            else:
                parsed_response = self.__parse_deidentify_file_response(response.data, run_id, response.data.status)
            log_info(SkyflowMessages.Info.GET_DETECT_RUN_SUCCESS.value,self.__vault_client.get_logger())
            return parsed_response
        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.DETECT_FILE_REQUEST_REJECTED.value,
                          self.__vault_client.get_logger())
            handle_exception(e, self.__vault_client.get_logger())

