# Migrate to the new Detect methods (skyflow 3.0.0)

The skyvault Python SDK replaces the previous Detect methods with the new Detect methods,
using the same method and class names as the flowvault Detect SDK — there is no version
suffix on any of them. `deidentify_file` keeps its name and now takes the new
`DeidentifyFileRequest`, returning the new `DeidentifyFileResponse`. Because the previous
methods and classes are removed, there is no name conflict. All Detect classes live in
`skyflow.vault.detect` and the enums in `skyflow.utils.enums`.

Callers of the previous Detect methods must migrate when they upgrade, so this ships in the
next major release, **skyflow 3.0.0** — pin or upgrade accordingly (`pip install "skyflow==3.0.0"`).
Client creation and the `skyflow_client.detect()` accessor do not change.

> **⚠️ Biggest behaviour change:** `deidentify_file` **no longer waits for the result by
> default.** It used to always poll; now, without `poll_options`, it submits and returns
> immediately — `status` is `None`, `output` is empty, and nothing is written to disk. Pass
> `poll_options` to block until the run finishes, or retrieve the result later with `get_run`.
> Code ported unchanged runs without error but produces no outputs, so the failure surfaces
> downstream rather than at the call site.

## What changes

|  | V1 | V2 |
| --- | --- | --- |
| Methods | `deidentify_text`, `reidentify_text`, `deidentify_file`, `get_detect_run` | `deidentify_string`, `reidentify_string`, `deidentify_file`, `reidentify_file`, `get_run`, `check_guardrails` |
| API | `/v1/detect/...`, one file endpoint per file type | `/v2/detect/...`, one file endpoint |
| Detection policy | flat fields on every request | a stored configuration id, or one inline `DetectConfiguration` |
| File polling | always, `wait_time` 1 to 64 s | opt in with `PollOptions`, `wait_time` 1 to 300 s and `max_attempts` 1 to 23 |
| New capabilities |  | reidentify file, guardrails, custom types, object entities (faces, logos), file mapping, `SKYFLOW_ID` and presigned URL inputs |

## Method mapping

| V1 method | V2 method | V2 request | V2 response |
| --- | --- | --- | --- |
| `deidentify_text(DeidentifyTextRequest)` | `deidentify_string(DeidentifyStringRequest)` | `DeidentifyStringRequest` | `DeidentifyStringResponse` |
| `reidentify_text(ReidentifyTextRequest)` | `reidentify_string(ReidentifyStringRequest)` | `ReidentifyStringRequest` | `ReidentifyStringResponse` |
| `deidentify_file(DeidentifyFileRequest)` | `deidentify_file(DeidentifyFileRequest)`, same name, new types | `DeidentifyFileRequest` | `DeidentifyFileResponse` |
| `get_detect_run(GetDetectRunRequest)` | `get_run(GetRunRequest)` | `GetRunRequest` | `GetRunResponse` |
| not available | `reidentify_file(ReidentifyFileRequest)` | `ReidentifyFileRequest` | `ReidentifyFileResponse` |
| not available | `check_guardrails(CheckGuardrailsRequest)` | `CheckGuardrailsRequest` | `CheckGuardrailsResponse` |

The file request and response keep their simple class names; only their shape changes.
Code that imported the V1 `DeidentifyFileRequest`/`DeidentifyFileResponse` keeps the
same import path (`skyflow.vault.detect`) but must be updated to the new fields.

## Step 1: Move the detection policy into a configuration

In V1 every call carried the policy as flat fields: `entities`, `token_format`,
`allow_regex_list`, `restrict_regex_list`, `transformations` and the media options. In
V2 the policy is a `DetectConfiguration`, supplied in one of two ways:

- `configuration_id`: a configuration created once in Studio or through the management
  API, then referenced by id. This is the recommended path.
- `configuration`: an inline `DetectConfiguration` built in code, for callers that need
  per-call control.

Exactly one of the two is expected. The SDK does not create, update or delete stored
configurations.

### Request field mapping

| V1 field | V2 equivalent |
| --- | --- |
| `entities=[DetectEntities...]` | `configuration.detect.entities`, one `Entity` per type with `entity_type` |
| `token_format.default` | an `Entity(entity_type=EntityType.ALL, deidentification_type=...)` placed last |
| `token_format.vault_token` | `Entity` per type with `deidentification_type=DeidentificationType.VAULT_TOKEN` and `destination="table.column"` |
| `token_format.entity_unique_counter` | `Entity` per type with `deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER` |
| `token_format.entity_only` | `Entity` per type with `deidentification_type=DeidentificationType.ENTITY_ONLY` |
| `allow_regex_list` | `configuration.detect.skip` |
| `restrict_regex_list` | `configuration.detect.restrict` |
| `transformations=Transformations(shift_dates=DateTransformation(max_days, min_days, entities))` | `transformation=Transformation(shift_dates=ShiftDates(min_days=, max_days=))` on each listed `Entity` |
| `pixel_density`, `max_resolution` | `configuration.media=Media(document=Document(pdf=Pdf(density=, max_resolution=)))` |
| `output_processed_image`, `output_ocr_text`, `masking_method` | `configuration.media=Media(image=Image(output_processed_image=, output_ocr_text=, masking_method=))` |
| `output_processed_audio`, `output_transcription` | `configuration.media=Media(audio=Audio(output_processed_audio=, output_transcription=))` |
| `bleep=Bleep(...)` | `configuration.media=Media(audio=Audio(bleep=Bleep(...)))` |
| `file=FileInput(file_path=path)` | `file=f` or `file_path=path` directly on the request |
| `wait_time` | `poll_options=PollOptions(wait_time=, max_attempts=)` |
| `output_directory` | `output_directory`, allowed only together with `poll_options` |

Enum renames:

- `DetectEntities` becomes `EntityType`, same values plus `NONE`.
- `TokenType` becomes `DeidentificationType` (`ENTITY_UNIQUE_COUNTER`, `ENTITY_ONLY`,
  `VAULT_TOKEN`, `MASK`).
- `DetectOutputTranscriptions` becomes `OutputTranscriptionType`.
- `MaskingMethod` keeps its name.
- Reidentify adds `RedactionType` (`PLAIN_TEXT`, `MASKED`, `REDACTED`, `DEFAULT`).

### Example: the same policy in V1 and V2

V1:

```python
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat, Transformations, DateTransformation
from skyflow.utils.enums import DetectEntities, TokenType

v1 = skyflow_client.detect().deidentify_text(DeidentifyTextRequest(
    text="My name is John Doe, and my email is johndoe@acme.com.",
    entities=[DetectEntities.NAME, DetectEntities.EMAIL_ADDRESS, DetectEntities.DOB],
    token_format=TokenFormat(default=TokenType.ENTITY_UNIQUE_COUNTER,
                             vault_token=[DetectEntities.NAME, DetectEntities.EMAIL_ADDRESS]),
    allow_regex_list=["Skyflow"],
    restrict_regex_list=["[0-9]{3}-[0-9]{2}-[0-9]{4}"],
    transformations=Transformations(shift_dates=DateTransformation(max_days=30, min_days=10,
                                                                   entities=[DetectEntities.DOB])),
))
```

V2, inline configuration:

```python
from skyflow.vault.detect import (
    DeidentifyStringRequest, DetectConfiguration, Detect, Entity, Transformation, ShiftDates,
)
from skyflow.utils.enums import EntityType, DeidentificationType

configuration = DetectConfiguration(detect=Detect(
    entities=[
        Entity(entity_type=EntityType.NAME, deidentification_type=DeidentificationType.VAULT_TOKEN, destination="persons.name"),
        Entity(entity_type=EntityType.EMAIL_ADDRESS, deidentification_type=DeidentificationType.VAULT_TOKEN, destination="persons.email"),
        Entity(entity_type=EntityType.DOB, deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER,
               transformation=Transformation(shift_dates=ShiftDates(min_days=10, max_days=30))),
        Entity(entity_type=EntityType.ALL, deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER),
    ],
    skip=["Skyflow"],
    restrict=["[0-9]{3}-[0-9]{2}-[0-9]{4}"],
))

v2 = skyflow_client.detect().deidentify_string(DeidentifyStringRequest(
    text="My name is John Doe, and my email is johndoe@acme.com.",
    configuration=configuration,
))
```

V2, stored configuration:

```python
v2 = skyflow_client.detect().deidentify_string(DeidentifyStringRequest(
    text="My name is John Doe, and my email is johndoe@acme.com.",
    configuration_id="<CONFIGURATION_ID>",
))
```

Two points that differ in meaning, not only in name:

- V1 listed `entities` once and then assigned token types per list. V2 states the
  `deidentification_type` on each entity. The V1 `token_format.default` becomes an
  `EntityType.ALL` entry placed last.
- V1 `vault_token` only named the entity types. V2 also needs a `destination` of the
  form `table.column` on each `VAULT_TOKEN` entity, which tells the vault where the
  value is stored.

## Step 2: deidentify_text to deidentify_string

```python
# V1
v1 = skyflow_client.detect().deidentify_text(request)
v1.processed_text
for e in v1.entities:
    e.entity; e.token; e.value
    e.text_index.start; e.text_index.end
    e.processed_index.start; e.processed_index.end
    e.scores
v1.word_count; v1.char_count

# V2
v2 = skyflow_client.detect().deidentify_string(request)
v2.processed_text
for e in v2.entities:
    e.entity_type; e.token; e.value
    e.location.start_index; e.location.end_index
    e.location.start_index_processed; e.location.end_index_processed
    e.entity_scores
v2.metrics.word_count; v2.metrics.character_count
```

| V1 response | V2 response |
| --- | --- |
| `entities` of `EntityInfo` | `entities` of `DetectedEntity` |
| `EntityInfo.entity` | `DetectedEntity.entity_type` |
| `text_index.start` / `.end` | `location.start_index` / `.end_index` |
| `processed_index.start` / `.end` | `location.start_index_processed` / `.end_index_processed` |
| `scores` | `entity_scores` |
| `word_count`, `char_count` | `metrics.word_count`, `metrics.character_count` |

`value` is populated in V2 only when the configuration sets `return_entities` to
`ReturnEntitiesType.ALL`. The default `EXCLUDE_SENSITIVE_DATA` returns an empty value.

## Step 3: reidentify_text to reidentify_string

V1 took three lists of entity types. V2 takes one list of `RedactionLevel` rules, each
naming an entity and a redaction type.

```python
# V1
from skyflow.vault.detect import ReidentifyTextRequest
from skyflow.utils.enums import DetectEntities

v1 = skyflow_client.detect().reidentify_text(ReidentifyTextRequest(
    text="My name is [NAME_1] and my email is [EMAIL_ADDRESS_1].",
    plain_text_entities=[DetectEntities.NAME],
    masked_entities=[DetectEntities.EMAIL_ADDRESS],
    redacted_entities=[DetectEntities.SSN],
))

# V2
from skyflow.vault.detect import ReidentifyStringRequest, RedactionLevel
from skyflow.utils.enums import EntityType, RedactionType

v2 = skyflow_client.detect().reidentify_string(ReidentifyStringRequest(
    text="My name is [NAME_1] and my email is [EMAIL_ADDRESS_1].",
    redaction_level=[
        RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT),
        RedactionLevel(entity_name=EntityType.EMAIL_ADDRESS, redaction_type=RedactionType.MASKED),
        RedactionLevel(entity_name=EntityType.SSN, redaction_type=RedactionType.REDACTED),
    ],
))
```

| V1 list | V2 rule |
| --- | --- |
| `plain_text_entities` | `RedactionLevel(entity_name=x, redaction_type=RedactionType.PLAIN_TEXT)` |
| `masked_entities` | `RedactionLevel(entity_name=x, redaction_type=RedactionType.MASKED)` |
| `redacted_entities` | `RedactionLevel(entity_name=x, redaction_type=RedactionType.REDACTED)` |

`processed_text` is unchanged. V2 adds `metrics`. The `token_group_name` and
`redaction_pattern` fields on `RedactionLevel` are for flowvault vaults and are not used
with skyvault.

## Step 4: deidentify_file, new request and response

The method keeps its name. The request and response classes keep their simple names but
change shape. Three things change at once: the file input, the policy, and the polling.

```python
# V1: always polls, first output only, in-memory File object
from skyflow.vault.detect import DeidentifyFileRequest, FileInput, TokenFormat
from skyflow.utils.enums import DetectEntities, TokenType

v1 = skyflow_client.detect().deidentify_file(DeidentifyFileRequest(
    file=FileInput(file_path="/data/intake/patient-notes.pdf"),
    entities=[DetectEntities.ALL],
    token_format=TokenFormat(default=TokenType.ENTITY_UNIQUE_COUNTER),
    pixel_density=200, max_resolution=3000,
    output_directory="/data/processed",
    wait_time=64,
))
v1.status; v1.file; v1.type; v1.extension; v1.entities; v1.page_count

# V2: same behaviour, opt in to polling, every output returned
from skyflow.vault.detect import DeidentifyFileRequest, PollOptions

v2 = skyflow_client.detect().deidentify_file(DeidentifyFileRequest(
    file_path="/data/intake/patient-notes.pdf",
    configuration_id="<CONFIGURATION_ID>",
    poll_options=PollOptions(wait_time=64),
    output_directory="/data/processed",
))
v2.status                                   # DetectRunStatus
for output in v2.output:                    # every output, not only the first
    output.processed_file; output.processed_file_type; output.processed_file_extension
v2.metrics.pages
```

Or submit only and retrieve later, which V1 could not do:

```python
submitted = skyflow_client.detect().deidentify_file(DeidentifyFileRequest(
    file_path="/data/intake/patient-notes.pdf",
    configuration_id="<CONFIGURATION_ID>",
))
run_id = submitted.run_id                   # status is None, nothing written to disk
```

### File response mapping

| V1 `DeidentifyFileResponse` | V2 `DeidentifyFileResponse` |
| --- | --- |
| `run_id` | `run_id` |
| `status` as `str` | `status` as `DetectRunStatus`, `None` when not polled |
| `file` (a `File`), `type`, `extension` for the first output | `output` list of `FileOutput` with `processed_file`, `processed_file_type`, `processed_file_extension` |
| `entities` as a list of dicts | entries in `output` whose `processed_file_type` is `ENTITIES` |
| `word_count`, `char_count` | `metrics.word_count`, `metrics.character_count` |
| `size_in_kb`, `duration_in_seconds` | `metrics.size`, `metrics.duration` |
| `page_count`, `slide_count` | `metrics.pages`, `metrics.slides` |
| not provided | `output_type`, `message` |

### Behaviour differences to check

- **Polling is opt in.** Without `poll_options` the call returns the run id
  immediately. V1 callers that relied on the result being complete must add
  `poll_options`.
- **Budget limits changed.** `wait_time` default 60 and maximum 300, where V1 defaulted
  to 64 and capped at 64. `max_attempts` is new, default and maximum 23.
- **All outputs are returned.** V1 surfaced only the first output through `file`. V2
  returns the full list in `output`.
- **Outputs are written only to `output_directory`.** V2 writes to `output_directory`,
  or the working directory when none is set, and only for local file inputs that reached
  `SUCCESS` with base64 outputs. Output names: redacted file
  `processed-<input name>.<extension>`, entities `processed-entities-<input name>.json`,
  object entities `processed-object-entities-<input name>.json`.
- **`UNKNOWN` ends polling.** Check for `DetectRunStatus.UNKNOWN` and call `get_run`
  later.
- **Validation is stricter.** `wait_time` and `max_attempts` out of range,
  `output_directory` without `poll_options`, and supplying both `file` and `value` fail
  before any network call.
- **Supported inputs widen.** `data_source` can be `DeidentifySourceType.SKYFLOW_ID`
  for a file already in the vault, or `DeidentifySourceType.PRESIGNED_URL`, in addition
  to a local `file`/`file_path`.

## Step 5: get_detect_run to get_run

```python
# V1
from skyflow.vault.detect import GetDetectRunRequest
run = skyflow_client.detect().get_detect_run(GetDetectRunRequest(run_id=run_id))

# V2
from skyflow.vault.detect import GetRunRequest
from skyflow.utils.enums import DetectRunStatus

run = skyflow_client.detect().get_run(GetRunRequest(run_id=run_id))
if run.status == DetectRunStatus.SUCCESS:
    for output in run.output:
        output.processed_file; output.processed_file_type; output.processed_file_extension
```

V1 returned the file response type. V2 returns `GetRunResponse`, which has the same
fields as the V2 `DeidentifyFileResponse` (`run_id`, `status`, `output_type`, `output`,
`metrics`, `message`). `get_run` writes nothing to disk.

## New in V2, no V1 equivalent

- `reidentify_file(ReidentifyFileRequest)`: re-identification of a file with the same
  `RedactionLevel` rules as strings.
- `check_guardrails(CheckGuardrailsRequest)`: toxicity and denied-topic screening.
  `check_toxicity` defaults to true on the server when omitted.
- `custom_types` on `Detect`: regex-defined entities with a label of your choosing.
- `object_entities` on `Detect`: `FACE`, `LICENSE_PLATE`, `LOGO` and `SIGNATURE`
  detection in images (`ObjectEntityType`).
- `return_entities` on `Detect`: control whether raw values come back
  (`ReturnEntitiesType`).
- `file_mapping` on `DetectConfiguration`: per-column handling for structured files.
- `processing_mode` on `Pdf`: `OCR` or `TEXT_LAYER` (`PdfProcessingMode`).

## Migration checklist

1. Create a stored Detect configuration in Studio that reproduces your V1 policy, or
   build it inline with `DetectConfiguration` using the field mapping above.
2. Rename the calls: `deidentify_text` to `deidentify_string`, `reidentify_text` to
   `reidentify_string`, `get_detect_run` to `get_run`. `deidentify_file` keeps its name;
   switch its request and response to the new fields.
3. Replace the V1 enums (`DetectEntities`, `TokenType`, `DetectOutputTranscriptions`)
   with the V2 enums (`EntityType`, `DeidentificationType`, `OutputTranscriptionType`),
   and add `RedactionType` for reidentify.
4. Add `poll_options` to every file call that expects a completed result.
5. Replace reads of `file`, `type`, `extension` and `entities` on file responses with a
   loop over `output`, and reads of flat metrics with `metrics`.
6. Switch reidentify calls from the three entity lists to `RedactionLevel` rules.
7. Handle `DetectRunStatus.UNKNOWN` and a `None` status on file responses.
8. Run the integration suite against the detect vault and compare outputs with the V1
   run for the same inputs.

## Timeline

| Release | Previous Detect methods | New Detect methods |
| --- | --- | --- |
| skyflow 2.1.x | available | not available |
| skyflow 3.0.0 | removed | available under the flowvault names |
