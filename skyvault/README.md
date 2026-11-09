# Skyflow Python SDK

> **This is the current, recommended version of the Skyflow SDK.** V2.1.0 brings flexible auth, multi-vault support, native data types, and rich error diagnostics.
>
> Migrating from v1? See the **[Migration Guide](https://github.com/skyflowapi/skyflow-python/blob/main/docs/migrate_to_v2.md)** for step-by-step instructions. V1 reached End of Life on October 31, 2026 and is no longer supported.

The Skyflow Python SDK is designed to help with integrating Skyflow into a Python backend.

## Table of Contents

- [Skyflow Python SDK](#skyflow-python-sdk)
    - [Table of Contents](#table-of-contents)
    - [Overview](#overview)
    - [Installation](#installation)
        - [Require](#require)
        - [Configuration](#configuration)
    - [Quickstart](#quickstart)
        - [Authenticate](#authenticate)
        - [API Key](#api-key)
        - [Bearer Token (static)](#bearer-token-static)
        - [Initialize the client](#initialize-the-client)
        - [Insert data into the vault, get tokens back](#insert-data-into-the-vault-get-tokens-back)
    - [Upgrade from v1 to v2](#upgrade-from-v1-to-v2)
    - [Vault](#vault)
        - [Insert and tokenize data: `.insert(request)`](#insert-and-tokenize-data-insertrequest)
            - [Insert example with `continue_on_error` option](#insert-example-with-continue_on_error-option)
            - [Upsert request](#upsert-request)
        - [Detokenize: `.detokenize(request, options)`](#detokenize-detokenizerequest-options)
            - [Construct a detokenize request](#construct-a-detokenize-request)
        - [Get Record(s): `.get(request)`](#get-records-getrequest)
            - [Construct a get request](#construct-a-get-request)
            - [Get by Skyflow IDs](#get-by-skyflow-ids)
            - [Get tokens for records](#get-tokens-for-records)
            - [Get by column name and column values](#get-by-column-name-and-column-values)
            - [Redaction Types](#redaction-types)
        - [Update Records](#update-records)
            - [Construct an update request](#construct-an-update-request)
        - [Delete Records](#delete-records)
        - [Query](#query)
        - [Upload File](#upload-file)
        - [Retrieve Existing Tokens: `.tokenize(request)`](#retrieve-existing-tokens-tokenizerequest)
            - [Construct a `.tokenize()` request](#construct-a-tokenize-request)
    - [Detect](#detect)
        - [Before you start](#before-you-start)
        - [De-identify String: `.deidentify_string(request)`](#de-identify-string-deidentify_stringrequest)
        - [Detect configuration](#detect-configuration)
        - [De-identify File: `.deidentify_file(request)`](#de-identify-file-deidentify_filerequest)
        - [Get Run: `.get_run(request)`](#get-run-get_runrequest)
        - [Re-identify String: `.reidentify_string(request)`](#re-identify-string-reidentify_stringrequest)
        - [Re-identify File: `.reidentify_file(request)`](#re-identify-file-reidentify_filerequest)
        - [Check Guardrails: `.check_guardrails(request)`](#check-guardrails-check_guardrailsrequest)
    - [Connections](#connections)
        - [Invoke a connection](#invoke-a-connection)
            - [Construct an invoke connection request](#construct-an-invoke-connection-request)
    - [Authentication & authorization](#authentication--authorization)
        - [Types of `credentials`](#types-of-credentials)
        - [Generate bearer tokens for authentication & authorization](#generate-bearer-tokens-for-authentication--authorization)
            - [Generate a bearer token](#generate-a-bearer-token)
                - [`generate_bearer_token(filepath)`](#generate_bearer_tokenfilepath)
                - [`generate_bearer_token_from_creds(credentials)`](#generate_bearer_token_from_credscredentials)
            - [Generate bearer tokens scoped to certain roles](#generate-bearer-tokens-scoped-to-certain-roles)
            - [Generate bearer tokens with `ctx` for context-aware authorization](#generate-bearer-tokens-with-ctx-for-context-aware-authorization)
            - [Generate signed data tokens: `generate_signed_data_tokens(filepath, options)`](#generate-signed-data-tokens-generate_signed_data_tokensfilepath-options)
    - [Logging](#logging)
        - [Example: Setting LogLevel to INFO](#example-setting-loglevel-to-info)
    - [Error handling](#error-handling)
        - [Catching `SkyflowError` instances](#catching-skyflowerror-instances)
        - [Bearer token expiration edge cases](#bearer-token-expiration-edge-cases)
    - [Security](#security)
        - [Reporting a Vulnerability](#reporting-a-vulnerability)

## Overview

The Skyflow SDK enables you to connect to your Skyflow Vault(s) to securely handle sensitive data at rest, in-transit, and in-use.

> [!TIP]
> Looking for the full list of request parameters, response object attributes, enums, client-management methods, and Detect helper classes? See the **[API Reference](../docs/api_reference.md)**.

> [!IMPORTANT]  
> This readme documents SDK version 2.  
> For version 1 see the [v1.16.0 README](https://github.com/skyflowapi/skyflow-python/tree/v1).  
> For more information on how to migrate see [MIGRATE_TO_V2.md](../docs/migrate_to_v2.md).

## Installation

### Require

- Python 3.9 and above (tested with Python 3.9)

### Configuration

The package can be installed using pip:

```bash
pip install skyflow
```

## Quickstart

Get started quickly with the essential steps: authenticate, initialize the client, and perform a basic vault operation. This section shows you a minimal working example.

### Before you begin

To run the examples below, you need a Skyflow account and a few values from the Skyflow Studio console. If you don't have an account yet, [request a demo](https://www.skyflow.com/get-demo).

| Value | Where to find it |
|-------|------------------|
| `vault_id` | Your vault's details page in Skyflow Studio. |
| `cluster_id` | The first segment of your vault URL: `https://{cluster_id}.vault.skyflowapis.com`. |
| `env` | The environment your vault runs in — `Env.PROD`, `Env.SANDBOX`, `Env.DEV`, or `Env.STAGE` (defaults to `PROD`). |
| Credentials | Create a **service account** in Studio. Choose **API key** during creation for the simplest setup, or download the service-account `credentials.json` for token-based auth. See [Authentication & authorization](#authentication--authorization). |

The quickstart below assumes a table named `table1` with `card_number` and `cardholder_name` columns. Create a matching table (or adjust the table/column names to your schema) in your vault before running it. See the [Skyflow docs](https://docs.skyflow.com/) for creating vaults, tables, and service accounts.

### Authenticate

You can use an API key or a personal bearer token to directly authenticate and authorize requests with the SDK. Use API keys for long-term service authentication. Use bearer tokens for optimal security.

### API Key

```python
credentials = {
    "api_key": "<API_KEY>"
}
```

### Bearer Token (static)

```python
credentials = {
    "token": "<BEARER_TOKEN>"
}
```

For authenticating via generated bearer tokens including support for scoped tokens, context-aware access tokens, and more, refer to the [Authentication & Authorization](#authentication--authorization) section.

### Initialize the client

Initialize the Skyflow client first. You can specify different credential types during initialization.

```python
from skyflow import Skyflow, LogLevel, Env

# Configure vault
config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',
    'env': Env.PROD,
    'credentials': {
        'api_key': '<YOUR_API_KEY>'
    }
}

# Initialize Skyflow client
skyflow_client = (
    Skyflow.builder()
    .add_vault_config(config)
    .set_log_level(LogLevel.ERROR)
    .build()
)
```

See [docs/advanced_initialization.md](../docs/advanced_initialization.md) for advanced initialization examples including multiple vaults and different credential types.

### Insert data into the vault, get tokens back

Insert data into your vault using the `insert` method. Set `return_tokens=True` in the request to ensure values are tokenized in the response.

Create an insert request with the [`InsertRequest`](../docs/api_reference.md#insertrequest) class, which includes the values to be inserted as a list of records.

Below is a simple example to get started. See the [Insert and tokenize data](#insert-and-tokenize-data-insertrequest) section for advanced options.

```python
from skyflow.vault.data import InsertRequest

# Insert sensitive data into the vault
insert_data = [
    { 'card_number': '4111111111111111', 'cardholder_name': 'John Doe' },
]

insert_request = InsertRequest(
    table='table1', 
    values=insert_data, 
    return_tokens=True
)

insert_response = skyflow_client.vault('<VAULT_ID>').insert(insert_request)
print('Insert response:', insert_response)
```

Returns an [`InsertResponse`](../docs/api_reference.md#insertresponse) (`inserted_fields`, `errors`). With `return_tokens=True`, each entry includes the `skyflow_id` and a token per column:

```text
Insert response: InsertResponse(inserted_fields=[{'skyflow_id': 'a8f0c2e1-7b3d-4f9a-8c21-1d2e3f4a5b6c', 'card_number': '5391-4629-3722-7102', 'cardholder_name': '0f6b8a2c-90ab-4cde-9def-567890abcdef'}], errors=None)
```

## Upgrade from v1 to v2

Upgrade from `skyflow-python` v1 using the dedicated guide in [docs/migrate_to_v2.md](../docs/migrate_to_v2.md).

## Vault

The [Vault](https://docs.skyflow.com/docs/vaults) performs operations on the vault, including inserting records, detokenizing tokens, and retrieving tokens associated with a skyflow_id.

### Insert and tokenize data: `.insert(request)`

Pass options to the `insert` method to enable additional functionality such as returning tokenized data, upserting records, or allowing bulk operations to continue despite errors. See [Quickstart](#quickstart) for a basic example.

```python
from skyflow.vault.data import InsertRequest

insert_request = InsertRequest(
    table='table1', 
    values=[
        {
            '<FIELD_NAME_1>': '<VALUE_1>',
            '<FIELD_NAME_2>': '<VALUE_2>'
        },
        {
            '<FIELD_NAME_1>': '<VALUE_1>',
            '<FIELD_NAME_2>': '<VALUE_2>'
        }
    ],
    return_tokens=True
)

response = skyflow_client.vault('<VAULT_ID>').insert(insert_request)
print('Insert response:', response)
```

Returns an [`InsertResponse`](../docs/api_reference.md#insertresponse):

```text
Insert response: InsertResponse(inserted_fields=[{'skyflow_id': 'a8f0c2e1-7b3d-4f9a-8c21-1d2e3f4a5b6c', '<FIELD_NAME_1>': '<TOKEN_1>', '<FIELD_NAME_2>': '<TOKEN_2>'}], errors=None)
```

> With `continue_on_error=True`, each entry also carries a `request_index`, and `errors` is a list of `{request_index, request_id, error, http_code}` for the rows that failed.

#### Insert example with `continue_on_error` option

Set the `continue_on_error` flag to `True` to allow insert operations to proceed despite encountering partial errors.

> [!TIP]
> See the full example in the samples directory: [insert_records.py](samples/vault_api/insert_records.py)

#### Upsert request

Turn an insert into an 'update-or-insert' operation using the upsert option. The vault checks for an existing record with the same value in the specified column. If a match exists, the record updates; otherwise, a new record inserts.

```python
# Specify the column to use as the index for the upsert.
# Note: The column must have the `unique` constraint configured in the vault.
insert_request = InsertRequest(
    table='table1',
    values=insert_data,
    upsert='<UPSERT_COLUMN_NAME>' 
)
```

### Detokenize: `.detokenize(request, options)`

Convert tokens back into plaintext values (or masked values) using the `.detokenize()` method. Detokenization accepts tokens and returns values.

Create a detokenization request with the [`DetokenizeRequest`](../docs/api_reference.md#detokenizerequest) class, which requires a list of tokens and column groups as input.

Provide optional parameters such as the redaction type and the option to continue on error.

#### Construct a detokenize request

```python
from skyflow.vault.tokens import DetokenizeRequest
from skyflow.utils.enums import RedactionType

detokenize_request = DetokenizeRequest(
    data=[
        {'token': 'token1', 'redaction_type': RedactionType.PLAIN_TEXT},
        {'token': 'token2', 'redaction_type': RedactionType.PLAIN_TEXT}
    ],
    continue_on_error=True
)

response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
print('Detokenization response:', response)
```

Returns a [`DetokenizeResponse`](../docs/api_reference.md#detokenizeresponse) (`detokenized_fields`, `errors`); each field has `token`, `value`, and `type`:

```text
Detokenization response: DetokenizeResponse(detokenized_fields=[{'token': 'token1', 'value': '4111111111111111', 'type': 'STRING'}, {'token': 'token2', 'value': 'John Doe', 'type': 'STRING'}], errors=None)
```

> [!TIP]
> See the full example in the samples directory: [detokenize_records.py](samples/vault_api/detokenize_records.py)

### Get Record(s): `.get(request)`

Retrieve data using Skyflow IDs or unique column values with the `get` method. Create a get request with the [`GetRequest`](../docs/api_reference.md#getrequest) class, specifying parameters such as the table name, redaction type, Skyflow IDs, column names, and column values.

> [!NOTE]
> You can't use both Skyflow IDs and column name/value pairs in the same request.

#### Construct a get request

```python
from skyflow.vault.data import GetRequest
from skyflow.utils.enums import RedactionType

get_request = GetRequest(
    table='table1',
    ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>'],
    redaction_type=RedactionType.PLAIN_TEXT,
    return_tokens=False
)

response = skyflow_client.vault('<VAULT_ID>').get(get_request)
print('Get response:', response)
```

Returns a [`GetResponse`](../docs/api_reference.md#getresponse) (`data`, `errors`), where `data` is a list of record dicts:

```text
Get response: GetResponse(data=[{'skyflow_id': 'a8f0c2e1-7b3d-4f9a-8c21-1d2e3f4a5b6c', 'card_number': '4111111111111111', 'cardholder_name': 'John Doe'}], errors=None)
```

#### Get by Skyflow IDs

Retrieve specific records using Skyflow IDs. Use this method when you know the exact record IDs.

```python
from skyflow.vault.data import GetRequest
from skyflow.utils.enums import RedactionType

get_request = GetRequest(
    table='table1',
    ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>'],
    redaction_type=RedactionType.PLAIN_TEXT
)

response = skyflow_client.vault('<VAULT_ID>').get(get_request)

print('Data retrieval successful:', response)
```

```text
Data retrieval successful: GetResponse(data=[{'skyflow_id': '<SKYFLOW_ID1>', 'card_number': '4111111111111111', 'cardholder_name': 'John Doe'}], errors=None)
```

#### Get tokens for records

Return tokens for records to securely process sensitive data while maintaining data privacy.

```python
get_request = GetRequest(
    table='table1',
    ids=['<SKYFLOW_ID1>'],
    return_tokens=True # Set to `True` to get tokens
)
```

> [!TIP]
> See the full example in the samples directory: [get_records.py](samples/vault_api/get_records.py)

#### Get by column name and column values

Retrieve records by unique column values when you don't know the Skyflow IDs. Use this method to query data with alternate unique identifiers.

```python
get_request = GetRequest(
    table='table1',
    column_name='email',
    column_values=['user@email.com'], # Column values of the records to return
)
```

> [!TIP]
> See the full example in the samples directory: [get_column_values.py](samples/vault_api/get_column_values.py)

#### Redaction Types

Use redaction types to control how sensitive data displays when retrieved from the vault.

**Available Redaction Types**

- `DEFAULT`: Applies the vault-configured default redaction setting.
- `REDACTED`: Completely removes sensitive data from view.
- `MASKED`: Partially obscures sensitive information.
- `PLAIN_TEXT`: Displays the full, unmasked data.

**Choosing the Right Redaction Type**

- Use `REDACTED` for scenarios requiring maximum data protection to prevent exposure of sensitive information.
- Use `MASKED` to provide partial visibility of sensitive data for less critical use cases.
- Use `PLAIN_TEXT` for internal, authorized access where full data visibility is necessary.

### Update Records

Update data in your vault using the `update` method. Create an update request with the [`UpdateRequest`](../docs/api_reference.md#updaterequest) class, specifying parameters such as the table name and data (as a dictionary).

You can pass options like `return_tokens` directly to the request. When `True`, Skyflow returns tokens for the updated records. When `False`, it returns IDs.

#### Construct an update request

```python
from skyflow.vault.data import UpdateRequest

update_request = UpdateRequest(
    table='table1', 
    data={
        'skyflow_id': '<SKYFLOW_ID>',
        '<COLUMN_NAME_1>': '<COLUMN_VALUE_1>',
        '<COLUMN_NAME_2>': '<COLUMN_VALUE_2>'
    }
)

response = skyflow_client.vault('<VAULT_ID>').update(update_request)
print('Update response:', response)
```

Returns an [`UpdateResponse`](../docs/api_reference.md#updateresponse) (`updated_field`, `errors`). With the default `return_tokens=False`, only the `skyflow_id` is returned; with `return_tokens=True`, tokens for the updated columns are included:

```text
Update response: UpdateResponse(updated_field={'skyflow_id': '<SKYFLOW_ID>'}, errors=None)
```

> [!TIP]
> See the full example in the samples directory: [update_record.py](samples/vault_api/update_record.py)

### Delete Records

Delete records using Skyflow IDs with the `delete` method. Create a delete request with the [`DeleteRequest`](../docs/api_reference.md#deleterequest) class, which accepts a list of Skyflow IDs:

```python
from skyflow.vault.data import DeleteRequest

delete_request = DeleteRequest(
    table='<TABLE_NAME>',
    ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>', '<SKYFLOW_ID3>']
)

response = skyflow_client.vault('<VAULT_ID>').delete(delete_request)
print('Delete response:', response)
```

Returns a [`DeleteResponse`](../docs/api_reference.md#deleteresponse) (`deleted_ids`, `errors`):

```text
Delete response: DeleteResponse(deleted_ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>', '<SKYFLOW_ID3>'], errors=None)
```

> [!TIP]
> See the full example in the samples directory: [delete_records.py](samples/vault_api/delete_records.py)

### Query

Retrieve data with SQL queries using the `query` method. Create a query request with the [`QueryRequest`](../docs/api_reference.md#queryrequest) class, which takes the `query` parameter as follows:

```python
from skyflow.vault.data import QueryRequest

query_request = QueryRequest(
    query="SELECT * FROM table1 WHERE column1 = 'value'"
)

response = skyflow_client.vault('<VAULT_ID>').query(query_request)
print('Query response:', response)
```

Returns a [`QueryResponse`](../docs/api_reference.md#queryresponse) (`fields`, `errors`), where `fields` is a list of matching record dicts (each also includes a `tokenized_data` map):

```text
Query response: QueryResponse(fields=[{'card_number': '4111111111111111', 'cardholder_name': 'John Doe', 'tokenized_data': {}}], errors=None)
```

> [!TIP]
> See the full example in the samples directory: [query_records.py](samples/vault_api/query_records.py)

Refer to [Query your data](https://docs.skyflow.com/query-data/) and [Execute Query](https://docs.skyflow.com/record/#QueryService_ExecuteQuery) for guidelines and restrictions on supported SQL statements, operators, and keywords.

### Upload File

Upload files to a Skyflow vault using the `upload_file` method. Create a file upload request with the [`FileUploadRequest`](../docs/api_reference.md#fileuploadrequest) class.

**Upload a file to an existing record:**

```python
from skyflow.vault.data import FileUploadRequest

# Open the file in binary read mode
with open('path/to/file.pdf', 'rb') as file_obj:
    upload_request = FileUploadRequest(
        table='<TABLE_NAME>',
        column_name='<COLUMN_NAME>',
        skyflow_id='<SKYFLOW_ID>',
        file_object=file_obj
    )

    response = skyflow_client.vault('<VAULT_ID>').upload_file(upload_request)
    print('File upload:', response)
```

**Upload a file and create a new record (omit `skyflow_id`):**

```python
with open('path/to/file.pdf', 'rb') as file_obj:
    upload_request = FileUploadRequest(
        table='documents',
        column_name='attachment',
        file_object=file_obj
    )

    response = skyflow_client.vault('<VAULT_ID>').upload_file(upload_request)
    print('File upload:', response)
```

Both forms return a [`FileUploadResponse`](../docs/api_reference.md#fileuploadresponse) (`skyflow_id`, `errors`) with the ID of the record the file was attached to (or the newly created record):

```text
File upload: FileUploadResponse(skyflow_id='a8f0c2e1-7b3d-4f9a-8c21-1d2e3f4a5b6c', errors=None)
```

> [!TIP]
> See the full example in the samples directory: [upload_file.py](samples/vault_api/upload_file.py)

### Retrieve Existing Tokens: `.tokenize(request)`

Retrieve tokens for values that already exist in the vault using the `.tokenize()` method. This method returns existing tokens only and does not generate new tokens. Build the request with the [`TokenizeRequest`](../docs/api_reference.md#tokenizerequest) class.

#### Construct a `.tokenize()` request

```python
from skyflow.vault.tokens import TokenizeRequest

tokenize_request = TokenizeRequest(
    values=[
        {"value": "<VALUE_1>", "column_group": "<COLUMN_GROUP_1>"},
        {"value": "<VALUE_2>", "column_group": "<COLUMN_GROUP_2>"}
    ]
)

response = skyflow_client.vault('<VAULT_ID>').tokenize(tokenize_request)
print('Tokenization result:', response)
```

Returns a [`TokenizeResponse`](../docs/api_reference.md#tokenizeresponse) (`tokenized_fields`, `errors`); each field carries its `token`:

```text
Tokenization result: TokenizeResponse(tokenized_fields=[{'token': 'a1b2c3d4-...'}, {'token': 'e5f6g7h8-...'}], errors=None)
```

> [!TIP]
> See the full example in the samples directory: [tokenize_records.py](samples/vault_api/tokenize_records.py)

## Detect

Skyflow Detect finds and de-identifies sensitive data in strings and files, re-identifies tokens on demand, and screens text against guardrails. The SDK exposes the Detect API through `DetectController`, returned by `skyflow_client.detect()` and `skyflow_client.detect('<VAULT_ID>')`. Every request is scoped to that vault, and the controller shares the same credentials, timeouts and retries as `vault()`; the `vault_id` is filled in from the vault config for every method.

Detect configurations are created in Studio or through the management API — the SDK does not create, update or delete them. Import request/response models from `skyflow.vault.detect` and enums from `skyflow.utils.enums`.

| Method | Request | Response | Description |
|--------|---------|----------|-------------|
| `deidentify_string(request)` | `DeidentifyStringRequest` | `DeidentifyStringResponse` | Detect and replace sensitive data in a string |
| `deidentify_file(request)` | `DeidentifyFileRequest` | `DeidentifyFileResponse` | Submit a file for de-identification, optionally polling the run to completion |
| `reidentify_string(request)` | `ReidentifyStringRequest` | `ReidentifyStringResponse` | Replace tokens in a string with their original or redacted values |
| `reidentify_file(request)` | `ReidentifyFileRequest` | `ReidentifyFileResponse` | Replace tokens in a file with their original or redacted values |
| `get_run(request)` | `GetRunRequest` | `GetRunResponse` | Retrieve the status and outputs of a Detect file run |
| `check_guardrails(request)` | `CheckGuardrailsRequest` | `CheckGuardrailsResponse` | Screen text for toxicity and denied topics |

```python
detect = skyflow_client.detect()
```

### Before you start

- **Role.** The service account needs the Detect Invoker, Detect Manager or Vault Owner role on the vault. Detect Invoker can de-identify data and write vault tokens into the vault; Detect Manager adds the ability to create, update and delete Detect configurations. Re-identifying values stored as `VAULT_TOKEN` is governed like detokenization: the caller also needs a policy granting the Detokenization action on the destination table and columns, unless it is a Vault Owner.
- **Configuration.** Pass `configuration_id` (the id of a stored Detect configuration) or an inline `configuration` (a `DetectConfiguration`). Both are optional: with neither set the SDK sends only the vault id and the run uses the vault's default Detect settings; sending both is rejected by the API with HTTP 400.
- **Destination for vault tokens.** An entity de-identified with `VAULT_TOKEN` stores its value in the `table.column` named by `destination` (for example `persons.ssn`). That table and column must already exist in the vault; Detect writes into them but does not create them.
- **API reference.** Every Detect request, response and configuration class is listed in the [API Reference](../docs/api_reference.md).

### De-identify String: `.deidentify_string(request)`

Synchronous. Detects and de-identifies sensitive data in a string. Build the request with `DeidentifyStringRequest`, passing the text and, optionally, one configuration source.

```python
from skyflow.vault.detect import DeidentifyStringRequest

response = skyflow_client.detect().deidentify_string(
    DeidentifyStringRequest(
        text='My name is John Doe, and my email is johndoe@acme.com.',
        configuration_id='<CONFIGURATION_ID>',
    )
)

print(response.processed_text)
# My name is [NAME_1], and my email is [EMAIL_ADDRESS_1].
for entity in response.entities:
    print(entity.entity_type, entity.token, entity.location.start_index, entity.entity_scores)
print(response.metrics.word_count)
```

An inline configuration is built from `DetectConfiguration` / `Detect` / `Entity` (see [Detect configuration](#detect-configuration)):

```python
from skyflow.vault.detect import DeidentifyStringRequest, DetectConfiguration, Detect, Entity
from skyflow.utils.enums import EntityType, DeidentificationType, ReturnEntitiesType

response = skyflow_client.detect().deidentify_string(
    DeidentifyStringRequest(
        text='My name is John Doe, and my email is johndoe@acme.com.',
        configuration=DetectConfiguration(
            detect=Detect(
                entities=[
                    Entity(entity_type=EntityType.NAME, deidentification_type=DeidentificationType.VAULT_TOKEN, destination='persons.name'),
                    Entity(entity_type=EntityType.ALL, deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER),
                ],
                skip=['Skyflow'],
                return_entities=ReturnEntitiesType.EXCLUDE_SENSITIVE_DATA,
            ),
        ),
    )
)
```

Returns a `DeidentifyStringResponse` with `processed_text`, `entities` (each a `DetectedEntity` with `token`, `value`, `location`, `entity_type`, `entity_scores`; never `None`) and `metrics`. `value` is populated only when the configuration sets `return_entities` to `ReturnEntitiesType.ALL`; the default `EXCLUDE_SENSITIVE_DATA` returns an empty `value`, so raw sensitive data does not come back unless you ask for it.

### Detect configuration

`DetectConfiguration` is the inline form of a stored configuration and accepts the same options. `detect` applies to string and file inputs; `file_mapping` and `media` apply to file inputs only.

| Class | Fields | Notes |
|-------|--------|-------|
| `Detect` | `entities`, `object_entities`, `restrict`, `skip`, `custom_types`, `return_entities` | `restrict` / `skip` are regexes always / never treated as sensitive. `return_entities` is `EXCLUDE_SENSITIVE_DATA` (server default), `ALL` or `NONE`. |
| `Entity` | `entity_type`, `deidentification_type`, `destination`, `transformation` | `entity_type` defaults to `ALL`. `deidentification_type` is `ENTITY_UNIQUE_COUNTER` (server default), `ENTITY_ONLY`, `MASK` or `VAULT_TOKEN`. `destination` (`table.column`) is used only with `VAULT_TOKEN`. |
| `Transformation` / `ShiftDates` | `shift_dates`; `min_days`, `max_days` | Shifts detected dates by a random number of days within the range. |
| `CustomType` | `label`, `match` | A regex-defined entity type; `label` is reported as the entity type of its matches. |
| `ObjectEntity` | `entity_type`, `deidentification_type` | Visual objects in images: `FACE`, `LICENSE_PLATE`, `LOGO`, `SIGNATURE` or `ALL`, handled with `REDACT` or `UNREDACT`. File inputs only. |
| `FileMapping` | `source`, `destination`, `output_file_name_suffix`, `entities_destination`, `object_entities_destination` | Where the processed file and entity files are written. File inputs only. |
| `Media` | `audio`, `document`, `image` | Media-type options. File inputs only. |
| `Audio` / `Bleep` | `output_processed_audio`, `output_transcription`, `bleep`; `start_padding`, `stop_padding`, `frequency`, `gain` | `output_transcription` is `NONE`, `TRANSCRIPTION`, `MEDICAL_TRANSCRIPTION`, `DIARIZED_TRANSCRIPTION` or `MEDICAL_DIARIZED_TRANSCRIPTION`. `Bleep` paddings are in seconds, frequency in Hz. |
| `Document` / `Pdf` | `pdf`; `processing_mode`, `density`, `max_resolution` | `processing_mode` is `NONE`, `OCR` or `TEXT_LAYER`. `density` is the rendering DPI. |
| `Image` | `output_processed_image`, `output_ocr_text`, `masking_method` | `masking_method` is `NONE`, `BLUR` or `BLACKBOX`. |

```python
from skyflow.vault.detect import (
    DetectConfiguration, Detect, Entity, Transformation, ShiftDates,
    CustomType, ObjectEntity, Media, Image, Document, Pdf, Audio, Bleep,
)
from skyflow.utils.enums import (
    EntityType, DeidentificationType, ObjectEntityType, ObjectDeidentificationType,
    MaskingMethod, PdfProcessingMode, OutputTranscriptionType,
)

configuration = DetectConfiguration(
    detect=Detect(
        entities=[
            Entity(
                entity_type=EntityType.DOB,
                deidentification_type=DeidentificationType.ENTITY_UNIQUE_COUNTER,
                transformation=Transformation(shift_dates=ShiftDates(min_days=10, max_days=30)),
            ),
            Entity(entity_type=EntityType.ALL),
        ],
        object_entities=[
            ObjectEntity(entity_type=ObjectEntityType.FACE, deidentification_type=ObjectDeidentificationType.REDACT),
        ],
        custom_types=[CustomType(label='EMPLOYEE_ID', match=['EMP-[0-9]{6}'])],
        restrict=['[0-9]{3}-[0-9]{2}-[0-9]{4}'],
    ),
    media=Media(
        image=Image(masking_method=MaskingMethod.BLUR, output_ocr_text=True),
        document=Document(pdf=Pdf(processing_mode=PdfProcessingMode.OCR)),
        audio=Audio(output_transcription=OutputTranscriptionType.TRANSCRIPTION, bleep=Bleep(start_padding=0.5, stop_padding=0.5)),
    ),
)
```

### De-identify File: `.deidentify_file(request)`

De-identifies a file. The API is asynchronous: the submit call returns a run id and the result is retrieved from the run. Build the request with `DeidentifyFileRequest`.

> **⚠️ Behaviour change from Detect V1:** `deidentify_file` **no longer waits for the result by default.** Without `poll_options` it submits and returns immediately — `status` is `None`, `output` is empty, and nothing is written to disk. Pass `poll_options` to block until the run finishes, or retrieve the result later with [`get_run`](#get-run-get_runrequest). Code ported from the old blocking behaviour runs without error but produces no outputs, so the failure surfaces downstream rather than at the call site.

Supply the file in exactly one of three ways: `file_path`, `file`, or `value` plus a `DeidentifySourceType` `data_source` (`BASE64`, the `SKYFLOW_ID` of a file record in the vault, or `PRESIGNED_URL`). A local `file` / `file_path` is read when the request is sent, base64-encoded, and its `data_format` inferred from the extension. Passing more than one of them, or none, fails client-side validation before any network call. `configuration_id` / `configuration` follow the same rules as for strings (see [Before you start](#before-you-start)).

- **Submit only** (default): one call, returns `run_id`. `status` is `None` and nothing is written to disk — retrieve the result later with [`get_run`](#get-run-get_runrequest).
- **Submit and poll**: pass `poll_options`. The SDK polls with exponential backoff (1, 2, 4, 8, 16, then 32 seconds) until the run is `SUCCESS`, `FAILED` or `UNKNOWN`, or until `wait_time` (default 60 s, max 300) or `max_attempts` (default and max 23) is used up. If the budget runs out the response carries the run id with `IN_PROGRESS` or `QUEUED`, so you can resume with `get_run`. `output_directory` is valid only with `poll_options`; setting it without them fails client-side validation.

```python
from skyflow.vault.detect import DeidentifyFileRequest, PollOptions
from skyflow.utils.enums import DetectRunStatus

# Submit only
submitted = skyflow_client.detect().deidentify_file(
    DeidentifyFileRequest(file_path='/data/intake/patient-notes.pdf', configuration_id='<CONFIGURATION_ID>')
)
run_id = submitted.run_id        # status is None; nothing written to disk

# Submit and poll
response = skyflow_client.detect().deidentify_file(
    DeidentifyFileRequest(
        file_path='/data/intake/patient-notes.pdf',
        configuration_id='<CONFIGURATION_ID>',
        poll_options=PollOptions(wait_time=120),
        output_directory='/data/processed',
    )
)

if response.status == DetectRunStatus.SUCCESS:
    for output in response.output:
        print(output.processed_file_type, output.processed_file_extension)
    print(response.metrics.pages)
elif response.status == DetectRunStatus.FAILED:
    print(response.message)
else:                            # IN_PROGRESS or QUEUED: budget ran out, resume with get_run(run_id)
    print(response.run_id)
```

**Where the outputs go.** On `SUCCESS`, when the request was built from a local `file` / `file_path` and the run returned base64 outputs, the SDK writes them to disk. With `output_directory='/data/processed'` the example above writes:

- `/data/processed/processed-patient-notes.pdf` — the redacted file
- `/data/processed/processed-entities-patient-notes.json` — the detected entities
- `/data/processed/processed-object-entities-patient-notes.json` — object entities, when the run produced them

`output_directory` is created if it does not exist. **If you poll a local file and omit `output_directory`, these files are written to the current working directory** — often your project root or a server's working directory — so set `output_directory` explicitly. A request built from a `SKYFLOW_ID` or `PRESIGNED_URL` value has no local name to derive from, and presigned-URL outputs are not fetched, so in those cases read `response.output` and write the files yourself.

**Supported formats and limits.** `data_format` accepts every `FileDataFormat`: `bmp`, `csv`, `dcm`, `doc`, `docx`, `gif`, `jpeg`, `jpg`, `json`, `jsonl`, `mp3`, `pdf`, `png`, `ppt`, `pptx`, `tif`, `tiff`, `txt`, `wav`, `xls`, `xlsx`, `xml`, `zip`. The `VAULT_TOKEN` de-identification type is supported only for `txt`, `csv`, `json`, `jsonl`, `xml`, `docx`, `xlsx` and `pptx`.

**Polling blocks the calling thread** — each lookup is a synchronous `get_run` followed by a sleep. For concurrency, submit without `poll_options` and poll `get_run` yourself on a scheduler, or run the blocking call on a worker thread you own.

A file at a presigned URL is referenced through `data_source` + `value`:

```python
from skyflow.vault.detect import DeidentifyFileRequest
from skyflow.utils.enums import DeidentifySourceType, FileDataFormat

skyflow_client.detect().deidentify_file(
    DeidentifyFileRequest(
        data_source=DeidentifySourceType.PRESIGNED_URL,
        value='<PRESIGNED_URL>',
        data_format=FileDataFormat.PDF,
        configuration_id='<CONFIGURATION_ID>',
    )
)
```

Returns a `DeidentifyFileResponse` with `run_id`, `status` (a `DetectRunStatus`, `None` when not polled), `output_type`, `output` (a list of `FileOutput` with `processed_file`, `processed_file_type`, `processed_file_extension`), `metrics` and `message`.

### Get Run: `.get_run(request)`

Retrieves the status and, once complete, the outputs of a Detect file run. Build the request with `GetRunRequest`, initialized with the `run_id` returned from a prior `deidentify_file` call. `output` is empty and `output_type` / `metrics` are `None` until the run completes.

```python
from skyflow.vault.detect import GetRunRequest
from skyflow.utils.enums import DetectRunStatus

run = skyflow_client.detect().get_run(GetRunRequest(run_id='<RUN_ID>'))

if run.status == DetectRunStatus.SUCCESS:
    for output in run.output:
        print(output.processed_file_type, output.processed_file_extension)
elif run.status == DetectRunStatus.FAILED:
    print(run.message)
else:                            # QUEUED, IN_PROGRESS, UNKNOWN: poll again later
    print(run.status)
```

Returns a `GetRunResponse` with the same fields as `DeidentifyFileResponse`.

### Re-identify String: `.reidentify_string(request)`

Synchronous. Re-identification looks tokens up in the vault, so it applies only to values de-identified with `VAULT_TOKEN`. Placeholders produced by `ENTITY_UNIQUE_COUNTER`, `ENTITY_ONLY` or `MASK` are not stored and cannot be re-identified.

Build the request with `ReidentifyStringRequest`: the tokenized text and an optional list of `RedactionLevel` rules. On skyvault vaults each rule names an `entity_name` and a `redaction_type` — `PLAIN_TEXT` reveals the original value, `MASKED` masks it, `REDACTED` keeps the token, `DEFAULT` applies the vault's default. Without rules every token is replaced by its original value.

Only text that contains vault tokens can be re-identified, so the example is a round trip: de-identify with `VAULT_TOKEN` (which stores each value in a `table.column`), then re-identify the `processed_text` that comes back. A vault token is an opaque value like `a1b2c3d4-...`, not the `[NAME_1]` counter placeholder produced by `ENTITY_UNIQUE_COUNTER`.

```python
from skyflow.vault.detect import (
    DeidentifyStringRequest, DetectConfiguration, Detect, Entity,
    ReidentifyStringRequest, RedactionLevel,
)
from skyflow.utils.enums import EntityType, DeidentificationType, RedactionType

# 1. De-identify with VAULT_TOKEN so each value is stored in a table.column and can be re-identified.
deidentified = skyflow_client.detect().deidentify_string(
    DeidentifyStringRequest(
        text='My name is John Doe and my email is johndoe@acme.com.',
        configuration=DetectConfiguration(detect=Detect(entities=[
            Entity(entity_type=EntityType.NAME, deidentification_type=DeidentificationType.VAULT_TOKEN, destination='persons.name'),
            Entity(entity_type=EntityType.EMAIL_ADDRESS, deidentification_type=DeidentificationType.VAULT_TOKEN, destination='persons.email'),
        ])),
    )
)
# deidentified.processed_text now holds vault tokens, e.g. 'My name is a1b2c3d4-... and my email is e5f6a7b8-...'

# 2. Re-identify those tokens; on skyvault each rule names an entity_name + redaction_type.
response = skyflow_client.detect().reidentify_string(
    ReidentifyStringRequest(
        text=deidentified.processed_text,
        redaction_level=[
            RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT),
            RedactionLevel(entity_name=EntityType.EMAIL_ADDRESS, redaction_type=RedactionType.MASKED),
        ],
    )
)
print(response.processed_text)
# My name is John Doe and my email is j*******@acme.com.
```

> The skyvault `RedactionLevel` has only `entity_name` and `redaction_type`; the flowvault SDK's has `token_group_name` and `redaction_pattern` instead.

Returns a `ReidentifyStringResponse` with `processed_text` and `metrics`.

### Re-identify File: `.reidentify_file(request)`

Synchronous — the re-identified file comes back in the response, not through a run id. Build the request with `ReidentifyFileRequest`: a `data_source` (`ReidentifySourceType.BASE64` or `PRESIGNED_URL`; re-identification does not accept a skyflow id as the source), the matching `value`, an optional `data_format`, and the same `RedactionLevel` rules as `reidentify_string`. `data_format` is limited to the formats that support `VAULT_TOKEN`: `txt`, `csv`, `json`, `jsonl`, `xml`, `docx`, `xlsx` and `pptx`.

```python
import base64
from skyflow.vault.detect import ReidentifyFileRequest, RedactionLevel
from skyflow.utils.enums import ReidentifySourceType, FileDataFormat, EntityType, RedactionType, DetectRunStatus

data_format = FileDataFormat.TXT
with open('/data/redacted/notes.txt', 'rb') as handle:
    encoded = base64.b64encode(handle.read()).decode('utf-8')

response = skyflow_client.detect().reidentify_file(
    ReidentifyFileRequest(
        data_source=ReidentifySourceType.BASE64,
        value=encoded,
        data_format=data_format,
        redaction_level=[RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT)],
    )
)

if response.status == DetectRunStatus.SUCCESS:
    for index, output in enumerate(response.output):
        # Branch on output_type: base64 bytes are decoded, a presigned URL is downloaded.
        if response.output_type == ReidentifySourceType.BASE64:
            with open(f'reidentified-{index}.{data_format.value}', 'wb') as out:
                out.write(base64.b64decode(output.processed_file))
        else:  # ReidentifySourceType.PRESIGNED_URL — processed_file is a URL to fetch
            print('download re-identified file from', output.processed_file)
```

Returns a `ReidentifyFileResponse` with `status`, `output_type` (a `ReidentifySourceType`), `output` (a list of `FileOutput`) and `metrics`.

### Check Guardrails: `.check_guardrails(request)`

Synchronous. Screens text for toxicity and a list of denied topics — a natural pre-LLM check. Build the request with `CheckGuardrailsRequest`. `check_toxicity` and `deny_topics` are optional; the SDK sends each only when set and fills in no default. **When `check_toxicity` is omitted, the server still checks toxicity by default.** The response is passed through as the API returns it.

```python
from skyflow.vault.detect import CheckGuardrailsRequest
from skyflow.utils.enums import GuardrailsValidation

response = skyflow_client.detect().check_guardrails(
    CheckGuardrailsRequest(text='<USER_PROMPT>', check_toxicity=True, deny_topics=['politics', 'medical advice'])
)

if response.validation == GuardrailsValidation.FAILED:
    print('blocked', response.toxic, response.denied_topic)
```

Returns a `CheckGuardrailsResponse` with `text`, `validation` (`GuardrailsValidation.PASSED` or `FAILED`), `toxic` and `denied_topic`.

All Detect methods raise `skyflow.error.SkyflowError` on validation failure, credential failure, or an API error — see [Error handling](#error-handling). Client-side validation fails before any network call.

## Connections

Securely send and receive data between your systems and first- or third-party services using Skyflow Connections. The [connections](https://github.com/skyflowapi/skyflow-python/tree/v2/skyflow/vault/connection) module invokes both inbound and/or outbound connections.

- **Inbound connections**: Act as intermediaries between your client and server, tokenizing sensitive data before it reaches your backend, ensuring downstream services handle only tokenized data.
- **Outbound connections**: Enable secure extraction of data from the vault and transfer it to third-party services via your backend server, such as processing checkout or card issuance flows.

### Invoke a connection

To invoke a connection, use the `invoke` method of the Skyflow client. Build the request with the [`InvokeConnectionRequest`](../docs/api_reference.md#invokeconnectionrequest) class.

#### Construct an invoke connection request

```python
from skyflow.vault.connection import InvokeConnectionRequest
from skyflow.utils.enums import RequestMethod

invoke_request = InvokeConnectionRequest(
    method=RequestMethod.POST,
    body={ '<COLUMN_NAME>': '<COLUMN_VALUE>' },
    headers={ '<HEADER_NAME>': '<HEADER_VALUE>' },
    path_params={ '<PATH_PARAM_KEY>': '<PATH_PARAM_VALUE>' },
    query_params={ '<QUERY_PARAM_KEY>': '<QUERY_PARAM_VALUE>' }
)

response = skyflow_client.connection().invoke(invoke_request)
print('Connection response:', response)
```

Returns an [`InvokeConnectionResponse`](../docs/api_reference.md#invokeconnectionresponse) (`data`, `metadata`, `errors`), where `data` is the connection's response body:

```text
Connection response: InvokeConnectionResponse(data={'message': 'success'}, metadata={'request_id': 'b7d3...'}, errors=None)
```

`method` supports the following methods (see [`RequestMethod`](../docs/api_reference.md#requestmethod)):

- `GET`
- `POST`
- `PUT`
- `DELETE`

**path_params, query_params, header, body** are the JSON objects represented as dictionaries that will be sent through the connection integration url.

> [!TIP]
> See the full example in the samples directory: [invoke_connection.py](samples/vault_api/invoke_connection.py)  
> See [docs.skyflow.com](https://docs.skyflow.com) for more details on integrations with Connections, Functions, and Pipelines.

## Authentication & authorization

### Types of `credentials`

The SDK accepts one of several types of credentials object.

1. **API keys**
   A unique identifier used to authenticate and authorize requests to an API. Use for long-term service authentication. To create an API key, first create a 'Service Account' in Skyflow and choose the 'API key' option during creation.

   ```python
   credentials = {
       "api_key": "<YOUR_API_KEY>"
   }
   ```

2. **Bearer tokens**
   A temporary access token used to authenticate API requests. Use for optimal security. As a developer with the right access, you can generate a temporary personal bearer token in Skyflow in the user menu.

   ```python
   credentials = {
    "token": "<YOUR_BEARER_TOKEN>"
    }
   ```

3. **Service account credentials file path**
   The file path pointing to a JSON file containing credentials for a service account. Use when credentials are managed externally or stored in secure file systems.

   ```python
   credentials = {
    "path": "<YOUR_CREDENTIALS_FILE_PATH>"
    }
   ```

4. **Service account credentials string**
   JSON-formatted string containing service account credentials. Use when integrating with secret management systems or when credentials are passed programmatically.

   ```python
   import os

   credentials = {
    "credentials_string": os.getenv("SKYFLOW_CREDENTIALS")
    }
   ```

5. **Environment variables**
   If no credentials are explicitly provided, the SDK automatically looks for the SKYFLOW_CREDENTIALS environment variable. Use to avoid hardcoding credentials in source code. This variable must return an object like one of the examples above.

> [!NOTE]
> Only one type of credential can be used at a time. If multiple credentials are provided, the last one added will take precedence.

### Generate bearer tokens for authentication & authorization

Generate and manage bearer tokens to authenticate API calls. This section covers options for scoping to certain roles, passing context, and signing data tokens.

#### Generate a bearer token

Generate service account tokens using the [Service Account](https://github.com/skyflowapi/skyflow-python/tree/main/skyflow/service_account) Python package with a service account credentials file provided when a service account is created. Tokens generated by this module are valid for 60 minutes and can be used to make API calls to the [Data](https://docs.skyflow.com/record/) and [Management](https://docs.skyflow.com/management/) APIs, depending on the permissions assigned to the service account.

##### `generate_bearer_token(filepath)`

The `generate_bearer_token(filepath)` function takes the `credentials.json` file path for token generation.

```python
from skyflow.service_account import generate_bearer_token

token, _ = generate_bearer_token('path/to/credentials.json')
print("Bearer Token:", token)
```

##### `generate_bearer_token_from_creds(credentials)`

Alternatively, you can also send the entire credentials as string by using `generate_bearer_token_from_creds(string)`.

> [!TIP]
> See the full example in the samples directory: [token_generation_example.py](https://github.com/skyflowapi/skyflow-python/blob/main/samples/service_account/token_generation_example.py)

#### Generate bearer tokens scoped to certain roles

Generate bearer tokens with access limited to a specific role by specifying the appropriate roleID when using a service account with multiple roles. Use this to limit access for services with multiple responsibilities, such as segregating access for billing and analytics. Generated bearer tokens are valid for 60 minutes and can only execute operations permitted by the permissions associated with the designated role.

```python
options = {
    'role_ids': ['roleID1', 'roleID2']
}
```

> [!TIP]
> See the full example in the samples directory: [scoped_token_generation_example.py](samples/service_account/scoped_token_generation_example.py)  
> See [docs.skyflow.com](https://docs.skyflow.com) for more details on authentication, access control, and governance for Skyflow.

#### Generate bearer tokens with `ctx` for context-aware authorization

Embed context values into a bearer token during generation so you can reference those values in your policies. This enables more flexible access controls, such as tracking end-user identity when making API calls using service accounts, and facilitates using signed data tokens during detokenization.

Generate bearer tokens containing context information using a service account with the `context_id` identifier. Context information is represented as a JWT claim in a Skyflow-generated bearer token. Tokens generated from such service accounts include a `context_identifier` claim, are valid for 60 minutes, and can be used to make API calls to the Data and Management APIs, depending on the service account's permissions.

The `ctx` parameter accepts either a **string** or a **dict**:

**String context** — use when your policy references a single context value:

```python
options = {'ctx': 'user_12345'}
token, _ = generate_bearer_token(filepath, options)
```

**Dict context** — use when your policy needs multiple context values for conditional data access. Each key in the dict maps to a Skyflow CEL policy variable under `request.context.*`:

```python
options = {
    'ctx': {
        'role': 'admin',
        'department': 'finance',
        'user_id': 'user_12345',
    }
}
token, _ = generate_bearer_token(filepath, options)
```

With the dict above, your Skyflow policies can reference `request.context.role`, `request.context.department`, and `request.context.user_id` to make conditional access decisions.

Dict keys must contain only alphanumeric characters and underscores (`[a-zA-Z0-9_]`). Invalid keys will raise a `SkyflowError`.

> [!TIP]
> See the full example in the samples directory: [token_generation_with_context_example.py](samples/service_account/token_generation_with_context_example.py)
> See Skyflow's [context-aware authorization](https://docs.skyflow.com) and [conditional data access](https://docs.skyflow.com) docs for policy variable syntax like `request.context.*`.

#### Generate signed data tokens: `generate_signed_data_tokens(filepath, options)`

Digitally sign data tokens with a service account's private key to add an extra layer of protection. Skyflow generates data tokens when sensitive data is inserted into the vault. Detokenize signed tokens only by providing the signed data token along with a bearer token generated from the service account's credentials. The service account must have the necessary permissions and context to successfully detokenize the signed data tokens.

The `ctx` parameter on signed data tokens also accepts either a **string** or a **dict**, using the same format as bearer tokens:

```python
# String context
options = {
    'ctx': 'user_12345',
    'data_tokens': ['dataToken1', 'dataToken2'],
    'time_to_live': 90,
}

# Dict context
options = {
    'ctx': {
        'role': 'analyst',
        'department': 'research',
    },
    'data_tokens': ['dataToken1', 'dataToken2'],
    'time_to_live': 90,
}
```

> [!TIP]
> See the full example in the samples directory: [signed_token_generation_example.py](samples/service_account/signed_token_generation_example.py)
> See [docs.skyflow.com](https://docs.skyflow.com) for more details on authentication, access control, and governance for Skyflow.

## Logging

The SDK provides logging using Python's inbuilt `logging` library. By default the logging level of the SDK is set to `LogLevel.ERROR`. This can be changed by using `set_log_level(log_level)` as shown below:

Currently, the following five log levels are supported:

- `DEBUG`:  
When `LogLevel.DEBUG` is passed, logs at all levels will be printed (DEBUG, INFO, WARN, ERROR).
- `INFO`:  
When `LogLevel.INFO` is passed, INFO logs for every event that occurs during SDK flow execution will be printed, along with WARN and ERROR logs.
- `WARN`:  
When `LogLevel.WARN` is passed, only WARN and ERROR logs will be printed.  
- `ERROR`:  
When `LogLevel.ERROR` is passed, only ERROR logs will be printed.
- `OFF`:
`LogLevel.OFF` can be used to turn off all logging from the Skyflow Python SDK.  

**Note:** The ranking of logging levels is as follows: `DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`.

### Example: Setting LogLevel to INFO

```python
from skyflow import Skyflow, LogLevel, Env

# Define vault configuration
vault_config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',
    'env': Env.PROD,
    'credentials': {'api_key': '<API_KEY>'}
}

skyflow_client = (
    Skyflow.builder()
    .add_vault_config(vault_config)
    .set_log_level(LogLevel.INFO) # Recommended to use LogLevel.ERROR in production
    .build()
)
```

## Using the client in production

**Build the client once and reuse it.** `Skyflow.builder()...build()` returns a long-lived client that lazily creates and caches an HTTP client and bearer token per vault. Construct it once at startup (for example, as a module-level singleton or a dependency-injected instance) and reuse it across requests. Rebuilding the client on every request discards these caches and forces unnecessary token regeneration.

```python
# At application startup
skyflow_client = (
    Skyflow.builder()
    .add_vault_config(vault_config)
    .set_log_level(LogLevel.ERROR)
    .build()
)

# Reuse `skyflow_client` for the lifetime of the process
```

**Bearer token refresh is automatic.** When you authenticate with a service-account credentials file/string (or API key), the SDK caches the generated bearer token and regenerates it automatically once it expires. You don't need to manage token lifecycle yourself for the common case. (For the rare expire-mid-request case, see [Bearer token expiration edge cases](#bearer-token-expiration-edge-cases).)

**Configuration mutation is not concurrency-safe.** Methods that change client configuration at runtime — `add_vault_config`, `update_vault_config`, `remove_vault_config`, the `*_connection_config` methods, and `update_skyflow_credentials` — mutate shared client state without locking. Perform configuration changes during setup, not concurrently with in-flight requests from other threads. Once configured, reusing the built client to issue operations is the intended usage pattern.

**Timeouts and retries.** The SDK does not currently expose request timeout or automatic-retry configuration. If you need strict timeout or retry guarantees, wrap your SDK calls with your own timeout/retry logic at the application layer.

## Error handling

### Catching `SkyflowError` instances

Wrap your calls to the Skyflow SDK in try/except blocks as a best practice. Use the `SkyflowError` class to identify errors coming from Skyflow versus general request/response errors.

```python
from skyflow.error import SkyflowError

try:
    # ...call the Skyflow SDK
    pass
except SkyflowError as error:
    # Handle Skyflow specific errors
    print("Skyflow Specific Error:", {
        "code": error.http_code,
        "message": error.message,
        "details": error.details,
    })
except Exception as error:
    # Handle generic errors
    print("Unexpected Error:", error)
```

### Bearer token expiration edge cases

When using bearer tokens for authentication and API requests, a token may expire after verification but before the actual API call completes. This causes the request to fail unexpectedly. An error from this edge case looks like this:

```txt
message: Authentication failed. Bearer token is expired. Use a valid bearer token. See https://docs.skyflow.com/api-authentication/
```

If you encounter this kind of error, retry the request. During the retry the SDK detects that the previous bearer token has expired and generates a new one for the current and subsequent requests.

> [!TIP]
> See the full example in the samples directory: [bearer_token_expiry_example.py](samples/service_account/bearer_token_expiry_example.py)  
> See [docs.skyflow.com](https://docs.skyflow.com) for more details on authentication, access control, and governance for Skyflow.

## Troubleshooting

Most first-run problems come from configuration mismatches. Every error raised by the SDK is a `SkyflowError` exposing `http_code`, `message`, and `details` — inspect these first (see [Error handling](#error-handling)).

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `pip install skyflow` fails / `RuntimeError: skyflow requires Python 3.9+` | Python older than 3.9 | Use Python 3.9 or above. |
| Connection/DNS failures, or 404 on every call | Wrong `cluster_id` | `cluster_id` is the first segment of your vault URL: `https://{cluster_id}.vault.skyflowapis.com`. |
| Requests hit the wrong host / unexpected auth failures | Wrong `env` | Match `env` to where your vault runs (`Env.PROD`, `Env.SANDBOX`, `Env.DEV`, `Env.STAGE`). |
| `401 Unauthorized` | Invalid or expired credentials | Verify your API key / service-account credentials. Regenerate if needed. |
| `403 Forbidden` | Service account lacks permission for the operation | Grant the service account a role with the required permissions, or use a [scoped token](#generate-bearer-tokens-scoped-to-certain-roles) with the right role. |
| `404` referencing a table or column | Table/column doesn't exist or name mismatch | Confirm the table and column names match your vault schema exactly (case-sensitive). |
| Vault not found / 404 with a valid `cluster_id` | Wrong `vault_id` | Copy `vault_id` from the vault's details page in Skyflow Studio. |
| `Authentication failed. Bearer token is expired.` | Token expired between verification and the API call | Retry the request; the SDK regenerates the token. See [Bearer token expiration edge cases](#bearer-token-expiration-edge-cases). |
| Unexpected credential is used | Multiple credentials provided | Only one credential type is used at a time; the last one added takes precedence. Provide exactly one. |
| `RequestMethod.PATCH` raises `AttributeError` | `PATCH` is not a supported connection method | Use `GET`, `POST`, `PUT`, or `DELETE` (see [`RequestMethod`](../docs/api_reference.md#requestmethod)). |

If you're stuck, set `set_log_level(LogLevel.DEBUG)` during development for detailed SDK logs (see [Logging](#logging)).

## Security

### Reporting a Vulnerability

If you discover a potential security issue in this project, reach out to us at [security@skyflow.com](mailto:security@skyflow.com). 

Don't create public GitHub issues or Pull Requests, as malicious actors could potentially view them.
