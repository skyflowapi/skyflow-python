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

### `FileInput`

`skyflow.vault.detect` — wrapper for a file passed to `DeidentifyFileRequest`. Provide one of:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file` | `None` | An open binary file (`BufferedReader`). |
| `file_path` | `None` | Path to a file. |

### `DeidentifyTextRequest`

`skyflow.vault.detect` — passed to `detect().deidentify_text()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | Text to de-identify. |
| `entities` | `None` | Entity types to detect. See `DetectEntities`. |
| `allow_regex_list` | `None` | Regex patterns to always treat as detectable. |
| `restrict_regex_list` | `None` | Regex patterns to exclude from detection. |
| `token_format` | `None` | `TokenFormat` controlling token types per entity. |
| `transformations` | `None` | `Transformations` (e.g. date shifting). |

### `DeidentifyFileRequest`

`skyflow.vault.detect` — passed to `detect().deidentify_file()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file` | `None` | A `FileInput`. |
| `entities` | `None` | Entity types to detect. |
| `allow_regex_list` | `None` | Regex patterns to always treat as detectable. |
| `restrict_regex_list` | `None` | Regex patterns to exclude. |
| `token_format` | `None` | `TokenFormat` per entity. |
| `transformations` | `None` | `Transformations` (not supported for Documents/Images/PDFs). |
| `output_processed_image` | `None` | Include the processed image in output. |
| `output_ocr_text` | `None` | Include OCR text in the response. |
| `masking_method` | `None` | See [`MaskingMethod`](#maskingmethod). |
| `pixel_density` | `None` | Pixel density for PDF processing. |
| `max_resolution` | `None` | Max resolution for PDF processing. |
| `output_processed_audio` | `None` | Include processed audio. |
| `output_transcription` | `None` | See [`DetectOutputTranscriptions`](#detectoutputtranscriptions). |
| `bleep` | `None` | Audio bleep config. See [`Bleep`](#bleep). |
| `output_directory` | `None` | Directory to write the processed file. |
| `wait_time` | `None` | Max seconds to wait (≤ 64). |

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

### `ReidentifyTextRequest`

`skyflow.vault.detect` — passed to `detect().reidentify_text()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | The redacted/de-identified text to re-identify. |
| `redacted_entities` | `None` | Entity types to keep redacted. See `DetectEntities`. |
| `masked_entities` | `None` | Entity types to mask. |
| `plain_text_entities` | `None` | Entity types to reveal as plain text. |

### `GetDetectRunRequest`

`skyflow.vault.detect` — passed to `detect().get_detect_run()`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `run_id` | _(required)_ | The `run_id` returned by a prior `deidentify_file` call. |

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

> **The `errors` attribute** is common to most responses. It is `list[dict] | None` and is populated only on partial failure (for example when `continue_on_error=True`); it is `None` when there are no errors. Each error dict contains `request_index`, `request_id`, `error`, and `http_code`. The per-class tables below describe only the operation-specific attributes and refer back to this note for `errors`.

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

### `DeidentifyTextResponse`

`skyflow.vault.detect` — returned by `detect().deidentify_text()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `processed_text` | `str` | The de-identified text. |
| `entities` | `list[EntityInfo]` | Detected entities. See [`EntityInfo`](#entityinfo). |
| `word_count` | `int` | Word count of the input text. |
| `char_count` | `int` | Character count of the input text. |
| `errors` | `list \| None` | See the note above. |

### `ReidentifyTextResponse`

`skyflow.vault.detect` — returned by `detect().reidentify_text()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `processed_text` | `str` | The re-identified text. |
| `errors` | `list \| None` | See the note above. |

### `DeidentifyFileResponse`

`skyflow.vault.detect` — returned by `detect().deidentify_file()` and `detect().get_detect_run()`. All non-error attributes are optional (default `None`) and are populated based on the file type and processing status. If processing exceeds `wait_time`, only `run_id` and `status` are set; poll with `get_detect_run`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_base64` | `str \| None` | The processed file as a base64 string. |
| `file` | `File \| None` | The processed file wrapper. See [`File`](#file). |
| `type` | `str \| None` | MIME type of the processed file. |
| `extension` | `str \| None` | File extension of the processed file. |
| `word_count` | `int \| None` | Word count (text-bearing files). |
| `char_count` | `int \| None` | Character count (text-bearing files). |
| `size_in_kb` | `float \| None` | Size of the processed file in KB. |
| `duration_in_seconds` | `float \| None` | Duration in seconds (audio files). |
| `page_count` | `int \| None` | Page count (PDF/document files). |
| `slide_count` | `int \| None` | Slide count (presentation files). |
| `entities` | `list[EntityInfo]` | Detected entities. Defaults to `[]`. See [`EntityInfo`](#entityinfo). |
| `run_id` | `str \| None` | Run identifier; pass to `get_detect_run` to poll for results. |
| `status` | `str \| None` | Processing status of the run. |
| `errors` | `list \| None` | See the note above. |

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

How retrieved data is displayed. Values: `PLAIN_TEXT`, `MASKED`, `DEFAULT`, `REDACTED`. See [Redaction Types](../README.md#redaction-types).

### `TokenMode`

Bring-your-own-token mode for `InsertRequest`/`UpdateRequest`.

| Member | Meaning |
|--------|---------|
| `DISABLE` | Do not accept caller-supplied tokens (default). |
| `ENABLE` | Accept caller-supplied tokens. |
| `ENABLE_STRICT` | Accept caller-supplied tokens with strict validation. |

### `TokenType`

Token format for Detect. Values: `VAULT_TOKEN` (`vault_token`), `ENTITY_UNIQUE_COUNTER` (`entity_unq_counter`), `ENTITY_ONLY` (`entity_only`).

### `ContentType`

Content type for connection requests. Values: `JSON`, `PLAINTEXT`, `XML`, `URLENCODED`, `FORMDATA`, `HTML`.

### `RequestMethod`

HTTP method for connections. Values: `GET`, `POST`, `PUT`, `DELETE`, `NONE`.

> Note: `PATCH` is **not** a member of this enum.

### `MaskingMethod`

Image masking method for Detect file de-identification. Values: `BLACKBOX` (`blackbox`), `BLUR` (`blur`).

### `DetectOutputTranscriptions`

Audio transcription output type for Detect. Values: `DIARIZED_TRANSCRIPTION`, `MEDICAL_DIARIZED_TRANSCRIPTION`, `MEDICAL_TRANSCRIPTION`, `TRANSCRIPTION`, `PLAINTEXT_TRANSCRIPTION`.

### `DetectEntities`

Entity types Detect can identify (e.g. `SSN`, `CREDIT_CARD`, `NAME`, `DOB`). Import from `skyflow.utils.enums`.

---

## Detect helper classes

Importable from `skyflow.vault.detect`.

### `EntityInfo`

A detected entity, returned inside `DeidentifyTextResponse.entities`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `token` | `str` | The token replacing the entity. |
| `value` | `str` | The original entity value. |
| `text_index` | `TextIndex` | Position in the input text. |
| `processed_index` | `TextIndex` | Position in the processed text. |
| `entity` | `str` | Entity type. |
| `scores` | `Dict[str, float]` | Confidence scores. |

### `TextIndex`

| Attribute | Type | Description |
|-----------|------|-------------|
| `start` | `int` | Start offset. |
| `end` | `int` | End offset. |

### `Bleep`

Audio bleep configuration for `DeidentifyFileRequest`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `gain` | `float` | Loudness in dB. |
| `frequency` | `float` | Pitch in Hz. |
| `start_padding` | `float` | Padding at start (seconds). |
| `stop_padding` | `float` | Padding at end (seconds). |

### `File`

Wrapper around the processed file returned in `DeidentifyFileResponse.file`.

| Member | Kind | Description |
|--------|------|-------------|
| `name` | property | File name. |
| `size` | property | Size in bytes. |
| `type` | property | MIME/type string. |
| `last_modified` | property | Last-modified timestamp. |
| `seek(offset, whence=0)` | method | Seek within the file. |
| `read(size=-1)` | method | Read file content. |

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
