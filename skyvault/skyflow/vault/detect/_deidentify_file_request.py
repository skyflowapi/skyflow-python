from typing import List, Optional, Union
from skyflow.utils.enums import DetectEntities
from skyflow.vault.detect import TokenFormat, Transformations
from skyflow.vault.detect._audio_bleep import Bleep
from skyflow.utils.enums import MaskingMethod, DetectOutputTranscriptions
from skyflow.vault.detect._file_input import FileInput

class DeidentifyFileRequest:
    def __init__(
        self,
        file = None,
        entities: Optional[List[DetectEntities]] = None,
        allow_regex_list: Optional[List[str]] = None,
        restrict_regex_list: Optional[List[str]] = None,
        token_format: Optional[TokenFormat] = None,
        transformations: Optional[Transformations] = None,
        output_processed_image: Optional[bool] = None,
        output_ocr_text: Optional[bool] = None,
        masking_method: Optional[MaskingMethod] = None,
        pixel_density: Optional[Union[int, float]] = None,
        max_resolution: Optional[Union[int, float]] = None,
        output_processed_audio: Optional[bool] = None,
        output_transcription: Optional[DetectOutputTranscriptions] = None,
        bleep: Optional[Bleep] = None,
        output_directory: Optional[str] = None,
        wait_time: Optional[Union[int, float]] = None
    ):
        self.file: FileInput = file
        self.entities: Optional[List[DetectEntities]] = entities
        self.allow_regex_list: Optional[List[str]] = allow_regex_list
        self.restrict_regex_list: Optional[List[str]] = restrict_regex_list
        self.token_format: Optional[TokenFormat] = token_format
        self.transformations: Optional[Transformations] = transformations
        self.output_processed_image: Optional[bool] = output_processed_image
        self.output_ocr_text: Optional[bool] = output_ocr_text
        self.masking_method: Optional[MaskingMethod] = masking_method
        self.pixel_density: Optional[Union[int, float]] = pixel_density
        self.max_resolution: Optional[Union[int, float]] = max_resolution
        self.output_processed_audio: Optional[bool] = output_processed_audio
        self.output_transcription: Optional[DetectOutputTranscriptions] = output_transcription
        self.bleep: Optional[Bleep] = bleep
        self.output_directory: Optional[str] = output_directory
        self.wait_time: Optional[Union[int, float]] = wait_time