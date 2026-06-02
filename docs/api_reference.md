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

### `InsertRequest` (`skyflow.vault.data`)

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

### `UpdateRequest` (`skyflow.vault.data`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `data` | _(required)_ | Dict containing `skyflow_id` and the columns to update. |
| `tokens` | `None` | BYOT values for the updated columns. |
| `return_tokens` | `False` | Return tokens (vs. IDs) for updated records. |
| `token_mode` | `TokenMode.DISABLE` | BYOT mode. See [`TokenMode`](#tokenmode). |

### `GetRequest` (`skyflow.vault.data`)

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

### `FileUploadRequest` (`skyflow.vault.data`)

Provide exactly one file source: `file_object`, `file_path`, or `base64`.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `table` | _(required)_ | Target table name. |
| `column_name` | `None` | File column name. |
| `skyflow_id` | `None` | Existing record ID. Omit to create a new record. |
| `file_path` | `None` | Path to a file to upload. |
| `base64` | `None` | Base64-encoded file content. |
| `file_object` | `None` | An open binary file object. |
| `file_name` | `None` | Override the file name. |

### `FileInput` (`skyflow.vault.detect`)

Wrapper for a file passed to `DeidentifyFileRequest`. Provide one of:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `file` | `None` | An open binary file (`BufferedReader`). |
| `file_path` | `None` | Path to a file. |

### `DeidentifyTextRequest` (`skyflow.vault.detect`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | _(required)_ | Text to de-identify. |
| `entities` | `None` | Entity types to detect. See `DetectEntities`. |
| `allow_regex_list` | `None` | Regex patterns to always treat as detectable. |
| `restrict_regex_list` | `None` | Regex patterns to exclude from detection. |
| `token_format` | `None` | `TokenFormat` controlling token types per entity. |
| `transformations` | `None` | `Transformations` (e.g. date shifting). |

### `DeidentifyFileRequest` (`skyflow.vault.detect`)

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

---

## Response objects

Every vault, token, connection, and Detect operation returns a typed response object. All carry an `errors` attribute that is populated on partial failure (`continue_on_error`).

| Response class | Module | Attributes |
|----------------|--------|------------|
| <a id="insertresponse"></a>`InsertResponse` | `skyflow.vault.data` | `inserted_fields`, `errors` |
| <a id="getresponse"></a>`GetResponse` | `skyflow.vault.data` | `data`, `errors` |
| <a id="deleteresponse"></a>`DeleteResponse` | `skyflow.vault.data` | `deleted_ids`, `errors` |
| <a id="updateresponse"></a>`UpdateResponse` | `skyflow.vault.data` | `updated_field`, `errors` |
| <a id="queryresponse"></a>`QueryResponse` | `skyflow.vault.data` | `fields`, `errors` |
| <a id="fileuploadresponse"></a>`FileUploadResponse` | `skyflow.vault.data` | `skyflow_id`, `errors` |
| <a id="detokenizeresponse"></a>`DetokenizeResponse` | `skyflow.vault.tokens` | `detokenized_fields`, `errors` |
| <a id="tokenizeresponse"></a>`TokenizeResponse` | `skyflow.vault.tokens` | `tokenized_fields`, `errors` |
| <a id="invokeconnectionresponse"></a>`InvokeConnectionResponse` | `skyflow.vault.connection` | `data`, `metadata`, `errors` |
| <a id="deidentifytextresponse"></a>`DeidentifyTextResponse` | `skyflow.vault.detect` | `processed_text`, `entities`, `word_count`, `char_count`, `errors` |
| <a id="reidentifytextresponse"></a>`ReidentifyTextResponse` | `skyflow.vault.detect` | `processed_text`, `errors` |
| <a id="deidentifyfileresponse"></a>`DeidentifyFileResponse` | `skyflow.vault.detect` | `file_base64`, `file`, `type`, `extension`, `word_count`, `char_count`, `size_in_kb`, `duration_in_seconds`, `page_count`, `slide_count`, `entities`, `run_id`, `status`, `errors` |

```python
response = skyflow_client.vault('<VAULT_ID>').insert(insert_request)
print(response.inserted_fields)  # list of inserted records (with tokens if return_tokens=True)
print(response.errors)           # populated only on partial failure
```

> `DeidentifyTextResponse.entities` is a list of [`EntityInfo`](#entityinfo). `DeidentifyFileResponse.file` is a [`File`](#file) wrapper.

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

HTTP method for connections. Values: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `NONE`.

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
