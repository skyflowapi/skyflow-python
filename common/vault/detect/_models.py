from __future__ import annotations

from typing import BinaryIO, Dict, List


class Metrics:
    def __init__(self, size: float = None, word_count: int = None,
                 character_count: int = None, slides: int = None,
                 pages: int = None, duration: float = None):
        self.size = size
        self.word_count = word_count
        self.character_count = character_count
        self.slides = slides
        self.pages = pages
        self.duration = duration


class FileOutput:
    def __init__(self, processed_file: str = None,
                 processed_file_type: str = None,
                 processed_file_extension: "FileDataFormat" = None):
        self.processed_file = processed_file
        self.processed_file_type = processed_file_type
        self.processed_file_extension = processed_file_extension


class RedactionLevel:
    def __init__(self, entity_name: "EntityType" = None,
                 redaction_type: "RedactionType" = None,
                 token_group_name: str = None,
                 redaction_pattern: str = None):
        self.entity_name = entity_name
        self.redaction_type = redaction_type
        self.token_group_name = token_group_name
        self.redaction_pattern = redaction_pattern


class ShiftDates:
    def __init__(self, min_days: int = None, max_days: int = None):
        self.min_days = min_days
        self.max_days = max_days


class Transformation:
    def __init__(self, shift_dates: ShiftDates = None):
        self.shift_dates = shift_dates


class Entity:
    def __init__(self, entity_type: "EntityType" = None,
                 deidentification_type: "DeidentificationType" = None,
                 destination: str = None,
                 transformation: Transformation = None):
        self.entity_type = entity_type
        self.deidentification_type = deidentification_type
        self.destination = destination
        self.transformation = transformation


class CustomType:
    def __init__(self, label: str = None, match: List[str] = None):
        self.label = label
        self.match = match


class ObjectEntity:
    def __init__(self, entity_type: "ObjectEntityType" = None,
                 deidentification_type: "ObjectDeidentificationType" = None):
        self.entity_type = entity_type
        self.deidentification_type = deidentification_type


class Detect:
    def __init__(self, entities: List[Entity] = None,
                 object_entities: List[ObjectEntity] = None,
                 restrict: List[str] = None, skip: List[str] = None,
                 custom_types: List[CustomType] = None,
                 return_entities: "ReturnEntitiesType" = None):
        self.entities = entities
        self.object_entities = object_entities
        self.restrict = restrict
        self.skip = skip
        self.custom_types = custom_types
        self.return_entities = return_entities


class FileMapping:
    def __init__(self, source: str = None, destination: str = None,
                 output_file_name_suffix: str = None,
                 entities_destination: str = None,
                 object_entities_destination: str = None):
        self.source = source
        self.destination = destination
        self.output_file_name_suffix = output_file_name_suffix
        self.entities_destination = entities_destination
        self.object_entities_destination = object_entities_destination


class Bleep:
    def __init__(self, start_padding: float = None, stop_padding: float = None,
                 frequency: int = None, gain: int = None):
        self.start_padding = start_padding
        self.stop_padding = stop_padding
        self.frequency = frequency
        self.gain = gain


class Audio:
    def __init__(self, output_processed_audio: bool = None,
                 output_transcription: "OutputTranscriptionType" = None,
                 bleep: Bleep = None):
        self.output_processed_audio = output_processed_audio
        self.output_transcription = output_transcription
        self.bleep = bleep


class Pdf:
    def __init__(self, processing_mode: "PdfProcessingMode" = None,
                 density: int = None, max_resolution: int = None):
        self.processing_mode = processing_mode
        self.density = density
        self.max_resolution = max_resolution


class Document:
    def __init__(self, pdf: Pdf = None):
        self.pdf = pdf


class Image:
    def __init__(self, output_processed_image: bool = None,
                 output_ocr_text: bool = None,
                 masking_method: "MaskingMethod" = None):
        self.output_processed_image = output_processed_image
        self.output_ocr_text = output_ocr_text
        self.masking_method = masking_method


class Media:
    def __init__(self, audio: Audio = None, document: Document = None,
                 image: Image = None):
        self.audio = audio
        self.document = document
        self.image = image


class DetectConfiguration:
    def __init__(self, name: str = None, description: str = None,
                 detect: Detect = None,
                 file_mapping: List[FileMapping] = None,
                 media: Media = None):
        self.name = name
        self.description = description
        self.detect = detect
        self.file_mapping = file_mapping
        self.media = media


class PollOptions:
    def __init__(self, wait_time: int = None, max_attempts: int = None):
        self.wait_time = wait_time
        self.max_attempts = max_attempts


class EntityLocation:
    def __init__(self, start_index: int = None, end_index: int = None,
                 start_index_processed: int = None,
                 end_index_processed: int = None):
        self.start_index = start_index
        self.end_index = end_index
        self.start_index_processed = start_index_processed
        self.end_index_processed = end_index_processed


class DetectedEntity:
    def __init__(self, token: str = None, value: str = None,
                 location: EntityLocation = None,
                 entity_type: str = None,
                 entity_scores: Dict[str, float] = None):
        self.token = token
        self.value = value
        self.location = location
        self.entity_type = entity_type
        self.entity_scores = entity_scores


class DeidentifyStringRequest:
    def __init__(self, text: str,
                 configuration_id: str = None,
                 configuration: DetectConfiguration = None):
        self.text = text
        self.configuration_id = configuration_id
        self.configuration = configuration


class DeidentifyStringResponse:
    def __init__(self, processed_text: str = None,
                 entities: List[DetectedEntity] = None,
                 metrics: Metrics = None):
        self.processed_text = processed_text
        self.entities = entities
        self.metrics = metrics


class DeidentifyFileRequest:
    def __init__(self, data_source: "DataSourceType" = None,
                 value: str = None,
                 data_format: "FileDataFormat" = None,
                 configuration_id: str = None,
                 configuration: DetectConfiguration = None,
                 file: BinaryIO = None, file_path: str = None,
                 poll_options: PollOptions = None,
                 output_directory: str = None):
        self.data_source = data_source
        self.value = value
        self.data_format = data_format
        self.configuration_id = configuration_id
        self.configuration = configuration
        self.file = file
        self.file_path = file_path
        self.poll_options = poll_options
        self.output_directory = output_directory


class DeidentifyFileResponse:
    def __init__(self, run_id: str = None,
                 status: "DetectRunStatus" = None,
                 output_type: "DataSourceType" = None,
                 output: List[FileOutput] = None,
                 metrics: Metrics = None,
                 message: str = None):
        self.run_id = run_id
        self.status = status
        self.output_type = output_type
        self.output = output
        self.metrics = metrics
        self.message = message


class GetRunRequest:
    def __init__(self, run_id: str):
        self.run_id = run_id


class GetRunResponse:
    def __init__(self, run_id: str = None,
                 status: "DetectRunStatus" = None,
                 output_type: "DataSourceType" = None,
                 output: List[FileOutput] = None,
                 metrics: Metrics = None,
                 message: str = None):
        self.run_id = run_id
        self.status = status
        self.output_type = output_type
        self.output = output
        self.metrics = metrics
        self.message = message


class ReidentifyStringRequest:
    def __init__(self, text: str,
                 redaction_level: List[RedactionLevel] = None):
        self.text = text
        self.redaction_level = redaction_level


class ReidentifyStringResponse:
    def __init__(self, processed_text: str = None, metrics: Metrics = None):
        self.processed_text = processed_text
        self.metrics = metrics


class ReidentifyFileRequest:
    def __init__(self, data_source: "DataSourceType" = None,
                 value: str = None,
                 data_format: "FileDataFormat" = None,
                 redaction_level: List[RedactionLevel] = None):
        self.data_source = data_source
        self.value = value
        self.data_format = data_format
        self.redaction_level = redaction_level


class ReidentifyFileResponse:
    def __init__(self, status: "DetectRunStatus" = None,
                 output_type: "DataSourceType" = None,
                 output: List[FileOutput] = None,
                 metrics: Metrics = None):
        self.status = status
        self.output_type = output_type
        self.output = output
        self.metrics = metrics


class CheckGuardrailsRequest:
    def __init__(self, text: str,
                 check_toxicity: bool = None,
                 deny_topics: List[str] = None):
        self.text = text
        self.check_toxicity = check_toxicity
        self.deny_topics = deny_topics


class CheckGuardrailsResponse:
    def __init__(self, text: str = None,
                 validation: "GuardrailsValidation" = None,
                 toxic: bool = None,
                 denied_topic: bool = None):
        self.text = text
        self.validation = validation
        self.toxic = toxic
        self.denied_topic = denied_topic
