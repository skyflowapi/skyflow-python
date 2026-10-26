from common.generated.rest.types import (
    DetectConfigV2 as WireDetectConfigV2,
    Detect as WireDetect,
    DetectEntity as WireDetectEntity,
    EntityTransformation as WireEntityTransformation,
    TransformationShiftDates as WireTransformationShiftDates,
    DetectCustomTypes as WireDetectCustomTypes,
    DetectObjectEntity as WireDetectObjectEntity,
    FileMapping as WireFileMapping,
    Media as WireMedia,
    AudioV2 as WireAudioV2,
    AudioV2Bleep as WireAudioV2Bleep,
    DocumentV2 as WireDocumentV2,
    DocumentV2Pdf as WireDocumentV2Pdf,
    ImageV2 as WireImageV2,
    RedactionLevel as WireRedactionLevel,
)
from common.utils.enums.detect import (
    DataSourceType,
    DetectRunStatus,
    FileDataFormat,
    GuardrailsValidation,
)

from ._constants import EXTENSION_SEPARATOR
from ._models import (
    CheckGuardrailsResponse,
    DeidentifyFileResponse,
    DeidentifyStringResponse,
    DetectedEntity,
    EntityLocation,
    FileOutput,
    GetRunResponse,
    Metrics,
    ReidentifyFileResponse,
    ReidentifyStringResponse,
)


def _omit_none(**kwargs):
    return {key: value for key, value in kwargs.items() if value is not None}


def _enum_value(member):
    return member.value if member is not None else None


def _enum_or_default(enum_cls, value, fallback):
    if value is None:
        return fallback
    try:
        return enum_cls(str(value))
    except ValueError:
        return fallback


def infer_format(file_name):
    if not file_name:
        return None
    index = file_name.rfind(EXTENSION_SEPARATOR)
    if index < 0 or index == len(file_name) - 1:
        return None
    try:
        return FileDataFormat[file_name[index + 1:].upper()]
    except KeyError:
        return None


def to_detect_config(configuration, vault_id):
    return WireDetectConfigV2(
        vault_id=vault_id,
        **_omit_none(
            name=configuration.name,
            description=configuration.description,
            detect=to_detect(configuration.detect) if configuration.detect is not None else None,
            file_mapping=to_file_mappings(configuration.file_mapping) if configuration.file_mapping is not None else None,
            media=to_media(configuration.media) if configuration.media is not None else None,
        ),
    )


def to_detect(detect):
    return WireDetect(**_omit_none(
        entities=[to_entity(entity) for entity in detect.entities if entity is not None] if detect.entities is not None else None,
        object_entities=[to_object_entity(obj) for obj in detect.object_entities if obj is not None] if detect.object_entities is not None else None,
        restrict=detect.restrict,
        skip=detect.skip,
        custom_types=[to_custom_type(custom) for custom in detect.custom_types if custom is not None] if detect.custom_types is not None else None,
        return_entities=_enum_value(detect.return_entities),
    ))


def to_entity(entity):
    return WireDetectEntity(**_omit_none(
        entity_type=_enum_value(entity.entity_type),
        deidentification_type=_enum_value(entity.deidentification_type),
        destination=entity.destination,
        transformation=to_transformation(entity.transformation) if entity.transformation is not None else None,
    ))


def to_transformation(transformation):
    shift_dates = transformation.shift_dates
    if shift_dates is None:
        return WireEntityTransformation()
    return WireEntityTransformation(shift_dates=WireTransformationShiftDates(**_omit_none(
        min_days=shift_dates.min_days,
        max_days=shift_dates.max_days,
    )))


def to_custom_type(custom_type):
    return WireDetectCustomTypes(**_omit_none(
        label=custom_type.label,
        match=custom_type.match,
    ))


def to_object_entity(object_entity):
    return WireDetectObjectEntity(**_omit_none(
        entity_type=_enum_value(object_entity.entity_type),
        deidentification_type=_enum_value(object_entity.deidentification_type),
    ))


def to_file_mappings(file_mappings):
    result = []
    for mapping in file_mappings:
        if mapping is None:
            continue
        result.append(WireFileMapping(**_omit_none(
            source=mapping.source,
            destination=mapping.destination,
            output_file_name_suffix=mapping.output_file_name_suffix,
            entities_destination=mapping.entities_destination,
            object_entities_destination=mapping.object_entities_destination,
        )))
    return result


def to_media(media):
    return WireMedia(**_omit_none(
        audio=to_audio(media.audio) if media.audio is not None else None,
        document=to_document(media.document) if media.document is not None else None,
        image=to_image(media.image) if media.image is not None else None,
    ))


def to_audio(audio):
    bleep = audio.bleep
    return WireAudioV2(**_omit_none(
        output_processed_audio=audio.output_processed_audio,
        output_transcription=_enum_value(audio.output_transcription),
        bleep=WireAudioV2Bleep(**_omit_none(
            start_padding=bleep.start_padding,
            stop_padding=bleep.stop_padding,
            frequency=bleep.frequency,
            gain=bleep.gain,
        )) if bleep is not None else None,
    ))


def to_document(document):
    pdf = document.pdf
    return WireDocumentV2(**_omit_none(
        pdf=WireDocumentV2Pdf(**_omit_none(
            processing_mode=_enum_value(pdf.processing_mode),
            density=pdf.density,
            max_resolution=pdf.max_resolution,
        )) if pdf is not None else None,
    ))


def to_image(image):
    return WireImageV2(**_omit_none(
        output_processed_image=image.output_processed_image,
        output_ocr_text=image.output_ocr_text,
        masking_method=_enum_value(image.masking_method),
    ))


def to_redaction_levels(levels):
    result = []
    for level in levels:
        if level is None:
            continue
        result.append(WireRedactionLevel(**_omit_none(
            entity_name=_enum_value(level.entity_name),
            redaction_type=_enum_value(level.redaction_type),
            token_group_name=level.token_group_name,
            redaction_pattern=level.redaction_pattern,
        )))
    return result


def to_metrics(metrics):
    return Metrics(
        size=metrics.size,
        word_count=metrics.word_count,
        character_count=metrics.character_count,
        slides=metrics.slides,
        pages=metrics.pages,
        duration=metrics.duration,
    )


def to_file_output(api_output):
    return FileOutput(
        processed_file=api_output.processed_file,
        processed_file_type=api_output.processed_file_type,
        processed_file_extension=_enum_or_default(FileDataFormat, api_output.processed_file_extension, None),
    )


def to_entity_location(location):
    return EntityLocation(
        start_index=location.start_index,
        end_index=location.end_index,
        start_index_processed=location.start_index_processed,
        end_index_processed=location.end_index_processed,
    )


def to_detected_entity(api_entity):
    scores = api_entity.entity_scores
    return DetectedEntity(
        token=api_entity.token,
        value=api_entity.value,
        location=to_entity_location(api_entity.location) if api_entity.location is not None else None,
        entity_type=api_entity.entity_type,
        entity_scores={} if scores is None else dict(scores),
    )


def to_deidentify_string_response(response):
    entities = [to_detected_entity(entity) for entity in (response.entities or []) if entity is not None]
    return DeidentifyStringResponse(
        processed_text=response.processed_text,
        entities=entities,
        metrics=to_metrics(response.metrics) if response.metrics is not None else None,
    )


def to_reidentify_string_response(response):
    return ReidentifyStringResponse(
        processed_text=response.processed_text,
        metrics=to_metrics(response.metrics) if response.metrics is not None else None,
    )


def to_check_guardrails_response(response):
    return CheckGuardrailsResponse(
        text=response.text,
        validation=_enum_or_default(GuardrailsValidation, response.validation, GuardrailsValidation.UNKNOWN),
        toxic=response.toxic,
        denied_topic=response.denied_topic,
    )


def to_get_run_response(run_id, response):
    outputs = [to_file_output(output) for output in (response.output or []) if output is not None]
    return GetRunResponse(
        run_id=run_id,
        status=_enum_or_default(DetectRunStatus, response.status, DetectRunStatus.UNKNOWN),
        output_type=_enum_or_default(DataSourceType, response.output_type, None),
        output=outputs,
        metrics=to_metrics(response.metrics) if response.metrics is not None else None,
        message=response.message,
    )


def submitted_deidentify_file_response(run_id):
    return DeidentifyFileResponse(run_id=run_id, status=None, output_type=None, output=[], metrics=None, message=None)


def to_deidentify_file_response(run_id, run):
    return DeidentifyFileResponse(
        run_id=run_id,
        status=run.status,
        output_type=run.output_type,
        output=run.output,
        metrics=run.metrics,
        message=run.message,
    )


def to_reidentify_file_response(response):
    outputs = [to_file_output(output) for output in (response.output or []) if output is not None]
    return ReidentifyFileResponse(
        status=_enum_or_default(DetectRunStatus, response.status, DetectRunStatus.UNKNOWN),
        output_type=_enum_or_default(DataSourceType, response.output_type, None),
        output=outputs,
        metrics=to_metrics(response.metrics) if response.metrics is not None else None,
    )
