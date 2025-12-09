# Skyflow Python SDK

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
        - [De-identify Text: `.deidentify_text(request)`](#de-identify-text-deidentify_textrequest)
        - [Re-identify Text: `.reidentify_text(request)`](#re-identify-text-reidentify_textrequest)
        - [De-identify File: `.deidentify_file(request)`](#de-identify-file-deidentify_filerequest)
        - [Get Run: `.get_detect_run(request)`](#get-run-get_detect_runrequest)
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

> [!IMPORTANT]  
> This readme documents SDK version 2.  
> For version 1 see the [v1.16.0 README](https://github.com/skyflowapi/skyflow-python/tree/v1).  
> For more information on how to migrate see [MIGRATE_TO_V2.md](docs/migrate_to_v2.md).

## Installation

### Require

- Python 3.8.0 and above (tested with Python 3.8.0)

### Configuration

The package can be installed using pip:

```bash
pip install skyflow
```

## Quickstart

Get started quickly with the essential steps: authenticate, initialize the client, and perform a basic vault operation. This section shows you a minimal working example.

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

See [docs/advanced_initialization.md](docs/advanced_initialization.md) for advanced initialization examples including multiple vaults and different credential types.

### Insert data into the vault, get tokens back

Insert data into your vault using the `insert` method. Set `return_tokens=True` in the request to ensure values are tokenized in the response.

Create an insert request with the `InsertRequest` class, which includes the values to be inserted as a list of records.

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

## Upgrade from v1 to v2

Upgrade from `skyflow-python` v1 using the dedicated guide in [docs/migrate_to_v2.md](docs/migrate_to_v2.md).

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

Create a detokenization request with the `DetokenizeRequest` class, which requires a list of tokens and column groups as input.

Provide optional parameters such as the redaction type and the option to continue on error.

#### Construct a detokenize request

```python
from skyflow.vault.tokens import DetokenizeRequest
from skyflow.utils.enums import RedactionType

detokenize_request = DetokenizeRequest(
    data=[
        {'token': 'token1', 'redaction': RedactionType.PLAIN_TEXT},
        {'token': 'token2', 'redaction': RedactionType.PLAIN_TEXT}
    ],
    continue_on_error=True
)

response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
print('Detokenization response:', response)
```

> [!TIP]
> See the full example in the samples directory: [detokenize_records.py](samples/vault_api/detokenize_records.py)

### Get Record(s): `.get(request)`

Retrieve data using Skyflow IDs or unique column values with the `get` method. Create a get request with the `GetRequest` class, specifying parameters such as the table name, redaction type, Skyflow IDs, column names, and column values.

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

Update data in your vault using the `update` method. Create an update request with the `UpdateRequest` class, specifying parameters such as the table name and data (as a dictionary).

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

> [!TIP]
> See the full example in the samples directory: [update_record.py](samples/vault_api/update_record.py)

### Delete Records

Delete records using Skyflow IDs with the `delete` method. Create a delete request with the `DeleteRequest` class, which accepts a list of Skyflow IDs:

```python
from skyflow.vault.data import DeleteRequest

delete_request = DeleteRequest(
    table='<TABLE_NAME>',
    ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>', '<SKYFLOW_ID3>']
)

response = skyflow_client.vault('<VAULT_ID>').delete(delete_request)
print('Delete response:', response)
```

> [!TIP]
> See the full example in the samples directory: [delete_records.py](samples/vault_api/delete_records.py)

### Query

Retrieve data with SQL queries using the `query` method. Create a query request with the `QueryRequest` class, which takes the `query` parameter as follows:

```python
from skyflow.vault.data import QueryRequest

query_request = QueryRequest(
    query="SELECT * FROM table1 WHERE column1 = 'value'"
)

response = skyflow_client.vault('<VAULT_ID>').query(query_request)
print('Query response:', response)
```

> [!TIP]
> See the full example in the samples directory: [query_records.py](samples/vault_api/query_records.py)

Refer to [Query your data](https://docs.skyflow.com/query-data/) and [Execute Query](https://docs.skyflow.com/record/#QueryService_ExecuteQuery) for guidelines and restrictions on supported SQL statements, operators, and keywords.

### Upload File

Upload files to a Skyflow vault using the `upload_file` method. Create a file upload request with the `FileUploadRequest` class, which accepts parameters such as the table name, column name, and Skyflow ID.

```python
from skyflow.vault.data import FileUploadRequest

# Open the file in binary read mode
with open('path/to/file.pdf', 'rb') as file_obj:
    upload_request = FileUploadRequest(
        table='documents', # Table name
        column_name='attachment', # Column name to store file
        skyflow_id='<SKYFLOW_ID>', # Skyflow ID of the record
        file_object=file_obj # Pass file object
    )
    
    # Perform File Upload
    response = skyflow_client.vault('<VAULT_ID>').upload_file(upload_request)
    print('File upload:', response)
```

> [!TIP]
> See the full example in the samples directory: [upload_file.py](samples/vault_api/upload_file.py)

### Retrieve Existing Tokens: `.tokenize(request)`

Retrieve tokens for values that already exist in the vault using the `.tokenize()` method. This method returns existing tokens only and does not generate new tokens.

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

> [!TIP]
> See the full example in the samples directory: [tokenize_records.py](samples/vault_api/tokenize_records.py)

## Detect

De-identify and reidentify sensitive data in text and files using Skyflow Detect, which supports advanced privacy-preserving workflows.

### De-identify Text: `.deidentify_text(request)`

De-identify or anonymize text using the `deidentify_text` method.

Create a de-identify text request with the `DeidentifyTextRequest` class.

```python
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat, Transformations, DateTransformation
from skyflow.utils.enums import DetectEntities, TokenType

request = DeidentifyTextRequest(
    text="<TEXT_TO_BE_DEIDENTIFIED>",
    entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
    token_format=TokenFormat(default=TokenType.VAULT_TOKEN),
    transformations=Transformations(
        shift_dates=DateTransformation(
            max_days=30, # Maximum days to shift
            min_days=10, # Minimum days to shift
            entities=[DetectEntities.DOB]
        )
    )
)

response = skyflow_client.detect('<VAULT_ID>').deidentify_text(request)
print('De-identify Text Response:', response)
```

> [!TIP]
> See the full example in the samples directory: [deidentify_text.py](samples/detect_api/deidentify_text.py)

### Re-identify Text: `.reidentify_text(request)`

Re-identify text using the `reidentify_text` method. Create a reidentify text request with the `ReidentifyTextRequest` class, which includes the redacted or de-identified text to be re-identified.

```python
from skyflow.vault.detect import ReidentifyTextRequest
from skyflow.utils.enums import DetectEntities

request = ReidentifyTextRequest(
    text="<REDACTED_TEXT_TO_REIDENTIFY>",
    redacted_entities=[DetectEntities.SSN],        # Keep redacted
    masked_entities=[DetectEntities.CREDIT_CARD],  # Mask
    plain_text_entities=[DetectEntities.NAME]      # Reveal
)

response = skyflow_client.detect().reidentify_text(request)
print('Re-identify Text Response:', response)
```

> [!TIP]
> See the full example in the samples directory: [reidentify_text.py](samples/detect_api/reidentify_text.py)

### De-identify File: `.deidentify_file(request)`

De-identify files using the `deidentify_file` method. Create a request with the `DeidentifyFileRequest` class, which includes the file to be deidentified. Provide optional parameters to control how entities are detected and deidentified.

```python
from skyflow.vault.detect import DeidentifyFileRequest, TokenFormat, FileInput
from skyflow.utils.enums import DetectEntities, TokenType

# Open file in binary mode
with open('path/to/file.pdf', 'rb') as file_obj:
    request = DeidentifyFileRequest(
        file=FileInput(file_obj),
        entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
        token_format=TokenFormat(default=TokenType.ENTITY_ONLY),
        output_directory='<OUTPUT_DIR>',
        wait_time=64
    )

    response = skyflow_client.detect().deidentify_file(request)
    print('De-identify File Response:', response)
```

**Supported file types:**

- Documents: `doc`, `docx`, `pdf`
- PDFs: `pdf`
- Images: `bmp`, `jpeg`, `jpg`, `png`, `tif`, `tiff`
- Structured text: `json`, `xml`
- Spreadsheets: `csv`, `xls`, `xlsx`
- Presentations: `ppt`, `pptx`
- Audio: `mp3`, `wav`

**Notes:**

- Transformations can't be applied to Documents, Images, or PDFs file formats.
- The `wait_time` option must be ≤ 64 seconds; otherwise, an error is thrown.
- If the API takes more than 64 seconds to process the file, it will return only the `run_id` and `status` in the response.

> [!TIP]
> See the full example in the samples directory: [deidentify_file.py](samples/detect_api/deidentify_file.py)

### Get Run: `.get_detect_run(request)`

Retrieve the results of a previously started file de-identification operation using the `get_detect_run` method. Initialize the request with the `run_id` returned from a prior .`deidentify_file` call.

```python
from skyflow.vault.detect import GetDetectRunRequest

request = GetDetectRunRequest(
    run_id='<RUN_ID_FROM_DEIDENTIFY_FILE>'
)

response = skyflow_client.detect().get_detect_run(request)
print('Get Detect Run Response:', response)
```

> [!TIP]
> See the full example in the samples directory: [get_detect_run.py](samples/detect_api/get_detect_run.py)

## Connections

Securely send and receive data between your systems and first- or third-party services using Skyflow Connections. The [connections](https://github.com/skyflowapi/skyflow-python/tree/v2/skyflow/vault/connection) module invokes both inbound and/or outbound connections.

- **Inbound connections**: Act as intermediaries between your client and server, tokenizing sensitive data before it reaches your backend, ensuring downstream services handle only tokenized data.
- **Outbound connections**: Enable secure extraction of data from the vault and transfer it to third-party services via your backend server, such as processing checkout or card issuance flows.

### Invoke a connection

To invoke a connection, use the `invoke` method of the Skyflow client.

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

`method` supports the following methods:

- `GET`
- `POST`
- `PUT`
- `PATCH`
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

Generate bearer tokens containing context information using a service account with the context_id identifier. Context information is represented as a JWT claim in a Skyflow-generated bearer token. Tokens generated from such service accounts include a context_identifier claim, are valid for 60 minutes, and can be used to make API calls to the Data and Management APIs, depending on the service account's permissions.

> [!TIP]
> See the full example in the samples directory: [token_generation_with_context_example.py](samples/service_account/token_generation_with_context_example.py)  
> See [docs.skyflow.com](https://docs.skyflow.com) for more details on authentication, access control, and governance for Skyflow.

#### Generate signed data tokens: `generate_signed_data_tokens(filepath, options)`

Digitally sign data tokens with a service account's private key to add an extra layer of protection. Skyflow generates data tokens when sensitive data is inserted into the vault. Detokenize signed tokens only by providing the signed data token along with a bearer token generated from the service account's credentials. The service account must have the necessary permissions and context to successfully detokenize the signed data tokens.

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

## Security

### Reporting a Vulnerability

If you discover a potential security issue in this project, reach out to us at [security@skyflow.com](mailto:security@skyflow.com). 

Don't create public GitHub issues or Pull Requests, as malicious actors could potentially view them.
