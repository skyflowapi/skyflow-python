# API Reference

A reference for the public Skyflow Python SDK surface: client-management methods, request and response objects, enums, Detect helper classes, and service-account functions. For task-oriented usage and examples, see the [README](../README.md).

All attributes, parameters, and enum values below are taken directly from the SDK source.

## Table of Contents

- [Client management methods](#client-management-methods)
- [Request objects](#request-objects)
- [Response objects](#response-objects)
- [Enums](#enums)
- [Detect helper classes](#detect-helper-classes)
- [Service account functions](#service-account-functions)

---

## Client management methods

In addition to the builder methods (`add_vault_config`, `add_connection_config`, `add_skyflow_credentials`, `set_log_level`, `build`) and the operation accessors (`vault()`, `connection()`, `detect()`), a built `Skyflow` client exposes methods to mutate its configuration and logging at runtime.

| Method | Purpose |
|--------|---------|
| `add_vault_config(config)` | Add a vault configuration after build. |
| `remove_vault_config(vault_id)` | Remove a vault configuration. |
| `update_vault_config(config)` | Update an existing vault configuration. |
| `get_vault_config(vault_id)` | Retrieve a vault configuration. |
| `add_connection_config(config)` | Add a connection configuration. |
| `remove_connection_config(connection_id)` | Remove a connection configuration. |
| `update_connection_config(config)` | Update a connection configuration. |
| `get_connection_config(connection_id)` | Retrieve a connection configuration. |
| `add_skyflow_credentials(credentials)` | Add common Skyflow credentials applied across configs. |
| `update_skyflow_credentials(credentials)` | Update the common Skyflow credentials. |
| `set_log_level(log_level)` | Set the log level (builder + client). |
| `update_log_level(log_level)` | Change the log level after initialization. |
| `get_log_level()` | Return the current log level. |
| `vault(vault_id=None)` | Get a vault controller for the given (or default) vault. |
| `connection(connection_id=None)` | Get a connection controller. |
| `detect(vault_id=None)` | Get a Detect controller. |

```python
# Example: manage configuration after the client is built
skyflow_client.add_vault_config(another_vault_config)
skyflow_client.update_log_level(LogLevel.DEBUG)
current_level = skyflow_client.get_log_level()
```

---

## Request objects

Parameters are listed with their defaults as defined in the constructors.

### `InsertRequest`

`skyflow.vault.data` — passed to `vault().insert()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `values` | _(required)_ | List of record dicts to insert. |
| `tokens` | `None` | Bring-your-own-token values, aligned with `values` (used with `token_mode`). |
| `upsert` | `None` | Column name to use as the upsert index (must have a `unique` constraint). |
| `homogeneous` | `False` | Treat the batch as homogeneous (all records share the same columns). |
| `token_mode` | `TokenMode.DISABLE` | BYOT mode. See [`TokenMode`](#tokenmode). |
| `return_tokens` | `True` | Return tokens for inserted values. |
| `continue_on_error` | `False` | Continue the batch despite partial errors. |

### `UpdateRequest`

`skyflow.vault.data` — passed to `vault().update()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `data` | _(required)_ | Dict containing `skyflow_id` and the columns to update. |
| `tokens` | `None` | BYOT values for the updated columns. |
| `return_tokens` | `False` | Return tokens (vs. IDs) for updated records. |
| `token_mode` | `TokenMode.DISABLE` | BYOT mode. See [`TokenMode`](#tokenmode). |

### `GetRequest`

`skyflow.vault.data` — passed to `vault().get()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `ids` | `None` | Skyflow IDs to retrieve. Mutually exclusive with `column_name`/`column_values`. |
| `redaction_type` | `None` | See [`RedactionType`](#redactiontype). |
| `return_tokens` | `False` | Return tokens instead of values. |
| `fields` | `None` | Specific fields/columns to return. |
| `offset` | `None` | Pagination offset. |
| `limit` | `None` | Pagination limit. |
| `download_url` | `None` | Return file download URLs for file columns. |
| `column_name` | `None` | Unique column to look up by. Mutually exclusive with `ids`. |
| `column_values` | `None` | Values for `column_name`. |

### `FileUploadRequest`

`skyflow.vault.data` — passed to `vault().upload_file()`. Provide exactly one file source: `file_object`, `file_path`, or `base64`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `column_name` | `None` | File column name. |
| `skyflow_id` | `None` | Existing record ID. Omit to create a new record. |
| `file_path` | `None` | Path to a file to upload. |
| `base64` | `None` | Base64-encoded file content. |
| `file_object` | `None` | An open binary file object. |
| `file_name` | `None` | Override the file name. |

### `DetokenizeRequest`

`skyflow.vault.tokens` — passed to `vault().detokenize()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `data` | _(required)_ | List of `{token, redaction_type}` dicts to detokenize. See [`RedactionType`](#redactiontype). |
| `continue_on_error` | `False` | Continue despite per-token errors. |

### `TokenizeRequest`

`skyflow.vault.tokens` — passed to `vault().tokenize()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `values` | _(required)_ | List of `{value, column_group}` dicts to tokenize. |

### `DeleteRequest`

`skyflow.vault.data` — passed to `vault().delete()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `ids` | _(required)_ | List of Skyflow IDs to delete. |

### `QueryRequest`

`skyflow.vault.data` — passed to `vault().query()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | _(required)_ | The SQL query string to execute. |

### `DeidentifyStringRequest`

`skyflow.vault.detect` — passed to `detect().deidentify_string()`. Set `configuration_id` or `configuration`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | Text to de-identify. Must be non-empty. |
| `configuration_id` | `None` | ID of an existing Detect configuration. |
| `configuration` | `None` | Inline configuration. See [`DetectConfiguration`](#detectconfiguration). |

### `DeidentifyFileRequest`

`skyflow.vault.detect` — passed to `detect().deidentify_file()`. Supply the file with `file_path`, `file`, or `data_source` and `value`. A local `file` or `file_path` can't be combined with `value`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file_path` | `None` | Path to a local file. The SDK base64-encodes it. |
| `file` | `None` | A local file opened in binary mode. The SDK base64-encodes it. If you also set `file_path`, the SDK reads `file_path`. |
| `data_source` | `None` | Source of `value`. See [`DataSourceType`](#datasourcetype). Required when you don't pass `file` or `file_path`. |
| `value` | `None` | Base64 content, Skyflow ID, or presigned URL, matching `data_source`. |
| `data_format` | `None` | Format of the input file. See [`FileDataFormat`](#filedataformat). Inferred from the file extension for a local file when not set. |
| `configuration_id` | `None` | ID of an existing Detect configuration. |
| `configuration` | `None` | Inline configuration. See [`DetectConfiguration`](#detectconfiguration). |
| `poll_options` | `None` | Poll the run until it finishes or the polling limits are reached. See [`PollOptions`](#polloptions). Without it, the call returns after submitting the run. |
| `output_directory` | `None` | Directory for processed outputs of a local file. Requires `poll_options`. |

### `GetRunRequest`

`skyflow.vault.detect` — passed to `detect().get_run()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `run_id` | _(required)_ | The `run_id` returned by `deidentify_file`. Must be non-empty. |

### `ReidentifyStringRequest`

`skyflow.vault.detect` — passed to `detect().reidentify_string()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | De-identified text to re-identify. Must be non-empty. |
| `redaction_level` | `None` | List of [`RedactionLevel`](#redactionlevel) objects that set how each entity type displays. |

### `ReidentifyFileRequest`

`skyflow.vault.detect` — passed to `detect().reidentify_file()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `data_source` | `None` | Source of `value`. See [`DataSourceType`](#datasourcetype). Required. |
| `value` | `None` | Base64 content, Skyflow ID, or presigned URL, matching `data_source`. Required. |
| `data_format` | `None` | Format of the input file: `txt`, `csv`, `json`, `xlsx`, `docx`, `pptx`, `xml`, or `jsonl`. See [`FileDataFormat`](#filedataformat). |
| `redaction_level` | `None` | List of [`RedactionLevel`](#redactionlevel) objects that set how each entity type displays. |

### `CheckGuardrailsRequest`

`skyflow.vault.detect` — passed to `detect().check_guardrails()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | Text to check. Must be non-empty. |
| `check_toxicity` | `None` | Set to `True` to check the text for toxicity. |
| `deny_topics` | `None` | List of topics to deny. |

### `InvokeConnectionRequest`

`skyflow.vault.connection` — passed to `connection().invoke()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `method` | _(required)_ | HTTP method. See [`RequestMethod`](#requestmethod). |
| `body` | `None` | Request body (dict). |
| `path_params` | `None` | Path parameters (dict). |
| `query_params` | `None` | Query parameters (dict). |
| `headers` | `None` | Request headers (dict). |

---

## Response objects

Every vault, token, connection, and Detect operation returns a typed response object. Each attribute below lists its type and meaning. Types use `| None` to mark attributes that may be absent.

> **The `errors` attribute** is common to the vault, token, and connection responses. It is `list[dict] | None` and is populated only on partial failure (for example when `continue_on_error=True`); it is `None` when there are no errors. Each error dict contains `request_index`, `request_id`, `error`, and `http_code`. The per-class tables below describe only the operation-specific attributes and refer back to this note for `errors`. Detect responses don't have an `errors` attribute; a failed Detect call raises `SkyflowError`.

```python
response = skyflow_client.vault('<VAULT_ID>').insert(insert_request)
print(response.inserted_fields)  # list of inserted records (with tokens if return_tokens=True)
print(response.errors)           # None unless there was a partial failure
```

### `InsertResponse`

`skyflow.vault.data` — returned by `vault().insert()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `inserted_fields` | `list[dict]` | One entry per inserted record. Each has `skyflow_id`; with `return_tokens=True`, also a token per column; with `continue_on_error=True`, also a `request_index`. |
| `errors` | `list[dict] \| None` | See the note above. |

### `GetResponse`

`skyflow.vault.data` — returned by `vault().get()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `list[dict]` | Retrieved records as `field → value` dicts (tokens instead of values when `return_tokens=True`). Defaults to `[]`. |
| `errors` | `list[dict] \| None` | See the note above. |

### `DeleteResponse`

`skyflow.vault.data` — returned by `vault().delete()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `deleted_ids` | `list[str] \| None` | Skyflow IDs of the deleted records. |
| `errors` | `list[dict] \| None` | See the note above. |

### `UpdateResponse`

`skyflow.vault.data` — returned by `vault().update()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `updated_field` | `dict` | The updated record: `skyflow_id`, plus a token per updated column when `return_tokens=True`. |
| `errors` | `list[dict] \| None` | See the note above. |

### `QueryResponse`

`skyflow.vault.data` — returned by `vault().query()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `fields` | `list[dict]` | Matching records. Each record dict also includes a `tokenized_data` map. |
| `errors` | `list[dict] \| None` | See the note above. |

### `FileUploadResponse`

`skyflow.vault.data` — returned by `vault().upload_file()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `skyflow_id` | `str` | ID of the record the file was attached to (or of the newly created record). |
| `errors` | `list[dict] \| None` | See the note above. |

### `DetokenizeResponse`

`skyflow.vault.tokens` — returned by `vault().detokenize()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `detokenized_fields` | `list[dict]` | One entry per token, each with `token`, `value` (plaintext or masked), and `type` (the value type). |
| `errors` | `list[dict] \| None` | See the note above. |

### `TokenizeResponse`

`skyflow.vault.tokens` — returned by `vault().tokenize()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `tokenized_fields` | `list[dict]` | One entry per value, each with its `token`. |
| `errors` | `list[dict] \| None` | See the note above. |

### `InvokeConnectionResponse`

`skyflow.vault.connection` — returned by `connection().invoke()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | The connection's response body. |
| `metadata` | `dict` | Response metadata (for example `request_id`). Defaults to `{}`. |
| `errors` | `list[dict] \| None` | See the note above. |

### `DeidentifyStringResponse`

`skyflow.vault.detect` — returned by `detect().deidentify_string()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `processed_text` | `str` | The de-identified text. |
| `entities` | `list[DetectedEntity]` | Detected entities. Defaults to `[]`. See [`DetectedEntity`](#detectedentity). |
| `metrics` | `Metrics \| None` | Processing metrics. See [`Metrics`](#metrics). |

### `DeidentifyFileResponse`

`skyflow.vault.detect` — returned by `detect().deidentify_file()`. Without `poll_options`, only `run_id` is set, `status` is `None`, and `output` is `[]`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | `str \| None` | Run identifier. Pass it to `get_run`. |
| `status` | `DetectRunStatus \| None` | Status of the run. See [`DetectRunStatus`](#detectrunstatus). |
| `output_type` | `DataSourceType \| None` | Form of the outputs. See [`DataSourceType`](#datasourcetype). |
| `output` | `list[FileOutput]` | Processed outputs. See [`FileOutput`](#fileoutput). |
| `metrics` | `Metrics \| None` | Processing metrics. See [`Metrics`](#metrics). |
| `message` | `str \| None` | Message returned for the run. |

### `GetRunResponse`

`skyflow.vault.detect` — returned by `detect().get_run()`. Has the same attributes as [`DeidentifyFileResponse`](#deidentifyfileresponse). A status the SDK doesn't recognize maps to `DetectRunStatus.UNKNOWN`.

### `ReidentifyStringResponse`

`skyflow.vault.detect` — returned by `detect().reidentify_string()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `processed_text` | `str` | The re-identified text. |
| `metrics` | `Metrics \| None` | Processing metrics. See [`Metrics`](#metrics). |

### `ReidentifyFileResponse`

`skyflow.vault.detect` — returned by `detect().reidentify_file()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `DetectRunStatus` | Status of the operation. See [`DetectRunStatus`](#detectrunstatus). |
| `output_type` | `DataSourceType \| None` | Form of the outputs. See [`DataSourceType`](#datasourcetype). |
| `output` | `list[FileOutput]` | Re-identified outputs. See [`FileOutput`](#fileoutput). |
| `metrics` | `Metrics \| None` | Processing metrics. See [`Metrics`](#metrics). |

### `CheckGuardrailsResponse`

`skyflow.vault.detect` — returned by `detect().check_guardrails()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text that was checked. |
| `validation` | `GuardrailsValidation` | Whether the text passed. See [`GuardrailsValidation`](#guardrailsvalidation). |
| `toxic` | `bool \| None` | Whether the text is toxic. |
| `denied_topic` | `bool \| None` | Whether the text includes a denied topic. |

---

## Enums

All enums are importable from `skyflow.utils.enums`.

### `Env`

Deployment environment. Values: `DEV`, `SANDBOX`, `PROD`, `STAGE`.

### `EnvUrls`

Vault hostnames per environment (used internally; exported for reference).

| Member | Host |
|--------|------|
| `PROD` | `vault.skyflowapis.com` |
| `SANDBOX` | `vault.skyflowapis-preview.com` |
| `DEV` | `vault.skyflowapis.dev` |
| `STAGE` | `vault.skyflowapis.tech` |

### `LogLevel`

`DEBUG`, `INFO`, `WARN`, `ERROR`, `OFF`. See [Logging](../README.md#logging).

### `RedactionType`

How retrieved or re-identified data is displayed. Used by `GetRequest`, `DetokenizeRequest`, and [`RedactionLevel`](#redactionlevel). Values: `PLAIN_TEXT`, `MASKED`, `DEFAULT`, `REDACTED`. See [Redaction Types](../skyvault/README.md#redaction-types).

### `TokenMode`

Bring-your-own-token mode for `InsertRequest`/`UpdateRequest`.

| Member | Meaning |
|--------|---------|
| `DISABLE` | Do not accept caller-supplied tokens (default). |
| `ENABLE` | Accept caller-supplied tokens. |
| `ENABLE_STRICT` | Accept caller-supplied tokens with strict validation. |

### `ContentType`

Content type for connection requests. Values: `JSON`, `PLAINTEXT`, `XML`, `URLENCODED`, `FORMDATA`, `HTML`.

### `RequestMethod`

HTTP method for connections. Values: `GET`, `POST`, `PUT`, `DELETE`, `NONE`.

> Note: `PATCH` is **not** a member of this enum.

### `EntityType`

Entity types for Detect, used in [`Entity`](#entity) and [`RedactionLevel`](#redactionlevel). Examples: `NAME`, `EMAIL_ADDRESS`, `SSN`, `CREDIT_CARD`, `DOB`, `PHONE_NUMBER`, `ALL`.

### `DeidentificationType`

How Detect de-identifies an entity. Values: `VAULT_TOKEN`, `ENTITY_UNIQUE_COUNTER`, `ENTITY_ONLY`, `MASK`, `UNKNOWN`. `VAULT_TOKEN` supports only `txt`, `json`, `csv`, `xml`, `jsonl`, `docx`, `xlsx`, and `pptx` files.

### `ReturnEntitiesType`

Which detected entities a de-identify response includes.

| Member | Meaning |
|--------|---------|
| `EXCLUDE_SENSITIVE_DATA` | Each entity's token, type, location, and scores, without the original value. |
| `ALL` | Each entity's metadata and the original value. |
| `NONE` | No entities. |

### `DataSourceType`

Source of a file `value`, and form of file outputs. Values: `BASE64`, `SKYFLOW_ID`, `PRESIGNED_URL`.

### `FileDataFormat`

File formats for Detect. Values: `BMP`, `CSV`, `DCM`, `DOC`, `DOCX`, `GIF`, `JPEG`, `JPG`, `JSON`, `JSONL`, `MP3`, `PDF`, `PNG`, `PPT`, `PPTX`, `TIF`, `TIFF`, `TXT`, `WAV`, `XLS`, `XLSX`, `XML`, `ZIP`. Each value is the lowercase extension, for example `FileDataFormat.PDF.value` is `pdf`.

### `DetectRunStatus`

Status of a Detect file run. Values: `QUEUED`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `UNKNOWN`. Polling stops at `SUCCESS`, `FAILED`, or `UNKNOWN`.

### `ObjectEntityType`

Object types for Detect to find. Values: `FACE`, `LICENSE_PLATE`, `LOGO`, `SIGNATURE`, `ALL`, `NONE`.

### `ObjectDeidentificationType`

How Detect handles a detected object. Values: `REDACT`, `UNREDACT`, `UNKNOWN`.

### `OutputTranscriptionType`

Audio transcription to include in the output. Values: `TRANSCRIPTION`, `MEDICAL_TRANSCRIPTION`, `DIARIZED_TRANSCRIPTION`, `MEDICAL_DIARIZED_TRANSCRIPTION`, `NONE`.

### `PdfProcessingMode`

How Detect processes a PDF. Values: `TEXT_LAYER` (process the PDF's text layer), `OCR` (process each page as an image, for scanned or image-based PDFs), `NONE`.

### `MaskingMethod`

How Detect masks entities in an image. Values: `BLUR`, `BLACKBOX`, `NONE`.

### `GuardrailsValidation`

Result of a guardrails check. Values: `PASSED`, `FAILED`, `UNKNOWN`.

---

## Detect helper classes

Importable from `skyflow.vault.detect`. Every parameter defaults to `None`.

### `DetectConfiguration`

An inline Detect configuration, passed as `configuration` to `deidentify_string` or `deidentify_file`. The SDK adds the vault ID from your vault configuration.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the configuration. |
| `description` | `str` | Description of the configuration. |
| `detect` | `Detect` | Entity detection and de-identification settings. See [`Detect`](#detect). |
| `file_mapping` | `list[FileMapping]` | Source and destination locations for files. See [`FileMapping`](#filemapping). |
| `media` | `Media` | Options for audio, documents, and images. See [`Media`](#media). |

### `Detect`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entities` | `list[Entity]` | Entity types to detect and how to de-identify each. See [`Entity`](#entity). |
| `object_entities` | `list[ObjectEntity]` | Object types to detect and how to handle each. See [`ObjectEntity`](#objectentity). |
| `restrict` | `list[str]` | Patterns for entities to replace with `[RESTRICTED]`. A pattern must match the entity's full value. |
| `skip` | `list[str]` | Patterns for entities to leave in plain text. A pattern can match the full value or a substring. `skip` takes precedence over `restrict`. |
| `custom_types` | `list[CustomType]` | Custom entity types. See [`CustomType`](#customtype). |
| `return_entities` | `ReturnEntitiesType` | Which detected entities the response includes. See [`ReturnEntitiesType`](#returnentitiestype). |

### `Entity`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_type` | `EntityType` | Entity type to detect. See [`EntityType`](#entitytype). |
| `deidentification_type` | `DeidentificationType` | How to de-identify the entity. See [`DeidentificationType`](#deidentificationtype). |
| `destination` | `str` | Vault column that stores detected values, in `table.column` format (for example, `persons.name`). |
| `transformation` | `Transformation` | Transformation to apply. See [`Transformation`](#transformation). |

### `Transformation`

| Parameter | Type | Description |
|-----------|------|-------------|
| `shift_dates` | `ShiftDates` | Shift dates within a range of days. See [`ShiftDates`](#shiftdates). |

### `ShiftDates`

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_days` | `int` | Minimum number of days to shift dates. |
| `max_days` | `int` | Maximum number of days to shift dates. |

### `ObjectEntity`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_type` | `ObjectEntityType` | Object to detect. See [`ObjectEntityType`](#objectentitytype). |
| `deidentification_type` | `ObjectDeidentificationType` | How to handle the object. See [`ObjectDeidentificationType`](#objectdeidentificationtype). |

### `CustomType`

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str` | Label of the custom type, used as its token prefix. |
| `match` | `list[str]` | Regular expressions. A detected entity that a pattern matches in full is replaced with `[<label>]`. |

### `FileMapping`

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str` | Location of the source file. |
| `destination` | `str` | Location of the target file. |
| `output_file_name_suffix` | `str` | Suffix for the output file name. For example, `_deidentified` turns `invoice.pdf` into `invoice_deidentified.pdf`. |
| `entities_destination` | `str` | Column for the entities output, in `table.column` format, in the same table as `source`. |
| `object_entities_destination` | `str` | Column for the object entities output, in `table.column` format, in the same table as `source`. |

### `Media`

| Parameter | Type | Description |
|-----------|------|-------------|
| `audio` | `Audio` | Audio options. See [`Audio`](#audio). |
| `document` | `Document` | Document options. See [`Document`](#document). |
| `image` | `Image` | Image options. See [`Image`](#image). |

### `Audio`

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_processed_audio` | `bool` | Include the processed audio in the output. Can't be combined with `output_transcription`. |
| `output_transcription` | `OutputTranscriptionType` | Transcription to include. See [`OutputTranscriptionType`](#outputtranscriptiontype). |
| `bleep` | `Bleep` | Bleep sound that masks entities. See [`Bleep`](#bleep). |

### `Bleep`

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_padding` | `float` | Padding before the bleep, in seconds (0–20). |
| `stop_padding` | `float` | Padding after the bleep, in seconds (0–20). |
| `frequency` | `int` | Frequency of the bleep, in Hz. |
| `gain` | `int` | Relative loudness. Positive values are louder; negative values are quieter. |

### `Document`

| Parameter | Type | Description |
|-----------|------|-------------|
| `pdf` | `Pdf` | PDF options. See [`Pdf`](#pdf). |

### `Pdf`

| Parameter | Type | Description |
|-----------|------|-------------|
| `processing_mode` | `PdfProcessingMode` | See [`PdfProcessingMode`](#pdfprocessingmode). |
| `density` | `int` | Pixel density. Applies only to `OCR` mode. |
| `max_resolution` | `int` | Maximum resolution. Applies only to `OCR` mode. |

### `Image`

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_processed_image` | `bool` | Include the processed image in the output. |
| `output_ocr_text` | `bool` | Include text detected by OCR in the output. |
| `masking_method` | `MaskingMethod` | See [`MaskingMethod`](#maskingmethod). |

### `PollOptions`

Polling limits for `deidentify_file`. The SDK waits 1, 2, 4, 8, 16, and then 32 seconds between attempts.

| Parameter | Type | Description |
|-----------|------|-------------|
| `wait_time` | `int` | Maximum total wait, in seconds. Default `60`, range 1–300. |
| `max_attempts` | `int` | Maximum number of status checks. Default `23`, range 1–23. |

### `RedactionLevel`

How one entity type displays in `reidentify_string` and `reidentify_file`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_name` | `EntityType` | Entity type to apply the setting to. See [`EntityType`](#entitytype). |
| `redaction_type` | `RedactionType` | How the value displays. See [`RedactionType`](#redactiontype). |

The class also accepts `token_group_name` and `redaction_pattern`, which apply to FlowVault vaults.

### `DetectedEntity`

A detected entity, returned in `DeidentifyStringResponse.entities`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `token` | `str` | The token that replaces the entity. |
| `value` | `str` | The original value. |
| `location` | `EntityLocation \| None` | Position in the input and processed text. See [`EntityLocation`](#entitylocation). |
| `entity_type` | `str` | The highest-rated entity type. |
| `entity_scores` | `dict[str, float]` | Entity types and their scores. Defaults to `{}`. |

### `EntityLocation`

| Attribute | Type | Description |
|-----------|------|-------------|
| `start_index` | `int` | Index of the first character in the input text. |
| `end_index` | `int` | Index of the last character in the input text. |
| `start_index_processed` | `int` | Index of the first character in the processed text. |
| `end_index_processed` | `int` | Index of the last character in the processed text. |

### `FileOutput`

A processed output, returned in the `output` list of file responses.

| Attribute | Type | Description |
|-----------|------|-------------|
| `processed_file` | `str` | The processed content. Base64-encoded when the response's `output_type` is `BASE64`. |
| `processed_file_type` | `str` | Kind of output, for example `REDACTED_FILE` or `ENTITIES`. |
| `processed_file_extension` | `FileDataFormat \| None` | Extension of the output. See [`FileDataFormat`](#filedataformat). |

### `Metrics`

| Attribute | Type | Description |
|-----------|------|-------------|
| `size` | `float` | Size of the input, in KB. |
| `word_count` | `int` | Number of words processed. |
| `character_count` | `int` | Number of characters processed. |
| `slides` | `int` | Number of slides processed. |
| `pages` | `int` | Number of pages processed. |
| `duration` | `float` | Duration processed, in seconds. |

---

## Service account functions

Importable from `skyflow.service_account`. See [Authentication & authorization](../README.md#authentication--authorization) for `generate_bearer_token`, `generate_bearer_token_from_creds`, and `generate_signed_data_tokens`.

### `is_expired(token, logger=None)`

Returns `True` if the given bearer token is expired (or `None`). Useful for caching tokens and only regenerating when needed.

```python
from skyflow.service_account import generate_bearer_token, is_expired

if cached_token is None or is_expired(cached_token):
    cached_token, _ = generate_bearer_token('path/to/credentials.json')
```

### `generate_signed_data_tokens_from_creds(credentials, options)`

The credentials-string counterpart to `generate_signed_data_tokens(filepath, options)`. Accepts a JSON credentials string instead of a file path; `options` is the same (`data_tokens`, `time_to_live`, `ctx`).

```python
import os
from skyflow.service_account import generate_signed_data_tokens_from_creds

signed_tokens = generate_signed_data_tokens_from_creds(
    os.getenv('SKYFLOW_CREDENTIALS'),
    {
        'data_tokens': ['dataToken1', 'dataToken2'],
        'time_to_live': 90,
        'ctx': 'user_12345',
    },
)
```
