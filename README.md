# Skyflow-python

---

## Description

This Python SDK is designed to help developers easily implement Skyflow into their python backend.

## Table of Contents

- [Skyflow-python](#skyflow-python)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
    - [Requirements](#requirements)
    - [Configuration](#configuration)
  - [Service Account Bearer Token Generation](#service-account-bearer-token-generation)
  - [Migration from v1 to v2](#migrate-from-v1-to-v2)
  - [Vault APIs](#vault-apis)
    - [Insert data into the vault](#insert-data-into-the-vault)
    - [Detokenize](#detokenize)
    - [Tokenize](#tokenize)
    - [Get](#get)
    - [Get By Id](#get-by-id)
      - [Redaction Types](#redaction-types)
    - [Update](#update)
    - [Delete](#delete)
    - [Invoke Connection](#invoke-connection)
    - [Query](#query)
  - [Logging](#logging)
  - [Reporting a Vulnerability](#reporting-a-vulnerability)

## Features

Authentication with a Skyflow Service Account and generation of a bearer token

Vault API operations to insert, retrieve and tokenize sensitive data

Invoking connections to call downstream third party APIs without directly handling sensitive data

## Installation

### Requirements

- Python 3.8.0 and above

### Configuration

The package can be installed using pip:

```bash
pip install skyflow
```

## Service Account Bearer Token Generation

The [Service Account](https://github.com/skyflowapi/skyflow-python/tree/main/skyflow/service_account) python module is used to generate service account tokens from service account credentials file which is downloaded upon creation of service account. The token generated from this module is valid for 60 minutes and can be used to make API calls to vault services as well as management API(s) based on the permissions of the service account.

The `generate_bearer_token(filepath)` function takes the credentials file path for token generation, alternatively, you can also send the entire credentials as string, by using `generate_bearer_token_from_creds(credentials)`

[Example using filepath](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
def token_provider():
    global bearer_token
    global token_type

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_toke('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

[Example using credentials string](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
def token_provider():
    global bearer_token
    global token_type
    # As an example
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
    credentials_string = json.dumps(skyflow_credentials)

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token_from_creds(skyflow_credentials_string)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

## Service Account Scoped Token Generation

[Example using filepath](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/scoped_token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'role_ids': ['ROLE_ID1', 'ROLE_ID2']
}
def token_provider():
    global bearer_token
    global token_type

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>', options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

[Example using credentials string](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/scoped_token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'role_ids': ['ROLE_ID1', 'ROLE_ID2']
}
def token_provider():
    global bearer_token
    global token_type
    # As an example
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
    credentials_string = json.dumps(skyflow_credentials)

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token_from_creds(skyflow_credentials_string, options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

## Service Account Token Generation With Context

[Example using filepath](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/token_generation_with_context_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'ctx': "<CONTEXT_ID>"
}
def token_provider():
    global bearer_token
    global token_type

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>', options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

[Example using credentials string](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/token_generation_with_context_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'ctx': '<CONTEXT_ID>'
}
def token_provider():
    global bearer_token
    global token_type
    # As an example
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
    credentials_string = json.dumps(skyflow_credentials)

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token_from_creds(skyflow_credentials_string, options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

## Service Account Signed Token Generation

[Example using filepath](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/signed_token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'ctx': 'CONTEX_ID',
    'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
    'time_to_live': 90 # in seconds
}
def token_provider():
    global bearer_token
    global token_type

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>', options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)

```

[Example using credentials string](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/service_account/signed_token_generation_example.py):

```python
from skyflow.error import SkyflowError
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired

# cache token for reuse
bearer_token = ''
token_type = ''
options = {
    'ctx': 'CONTEX_ID',
    'data_tokens': ['DATA_TOKEN1', 'DATA_TOKEN2'],
    'time_to_live': 90 # in seconds
}
def token_provider():
    global bearer_token
    global token_type
    # As an example
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
    credentials_string = json.dumps(skyflow_credentials)

    if is_expired(bearer_token):
        bearer_token, token_type = generate_bearer_token_from_creds(skyflow_credentials_string, options)
    return bearer_token, token_type

try:
    bearer_token, token_type = token_provider()
    print('Access Token:', bearer_token)
    print('Type of token:', token_type)
except SkyflowError as e:
    print(e)
```
## Migrate from V1 to V2

Below are the steps to migrate the Python SDK from V1 to V2.

### 1. Authentication Options

In V2, we have introduced multiple authentication options. 
You can now provide credentials in the following ways: 

- **API Key (Recommended)**
- **Environment Variable** (`SKYFLOW_CREDENTIALS`) (**Recommended**)
- **Path to your credentials JSON file**
- **Stringified JSON of your credentials**
- **Bearer token**

These options allow you to choose the authentication method that best suits your use case.

#### V1 (Old):
Passing the token provider function below as a parameter to the Configuration.

```python
# User defined function to provide access token to the vault apis
def token_provider():
    global bearerToken
    if !(is_expired(bearerToken)):
        return bearerToken
    bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken
```

#### V2 (New):
Passing one of the following:

```python
# Option 1: API Key (Recommended)
credentials = {
    'api_key': '<YOUR_API_KEY>', # API key
}

# Option 2: Environment Variables (Recommended)
# Set SKYFLOW_CREDENTIALS in your environment

# Option 3: Credentials File
credentials = {
    'path': '<PATH_TO_CREDENTIALS_JSON>', # Path to credentials file
}

# Option 4: Stringified JSON
credentials = {
    'credentials_string': '<YOUR_CREDENTIALS_sTRING>', # Credentials as string
}

# Option 5: Bearer Token
credentials = {
    'token': '<YOUR_BEARER_TOKEN>', # Bearer token
}
```

**Notes:**
- Use only ONE authentication method.
- API Key or Environment Variables are recommended for production use.
- Secure storage of credentials is essential.
- For overriding behavior and priority order of credentials, please refer to the README.

### 2. Client Initialization

In V2, we have introduced a Builder design pattern for client initialization and added support for multi-vault. This allows you to configure multiple vaults during client initialization. 

In V2, the log level is tied to each individual client instance. 

During client initialization, you can pass the following parameters:

- **`vault_id`** and **`cluster_id`**: These values are derived from the vault ID & vault URL.
- **`env`**: Specify the environment (e.g., SANDBOX or PROD).
- **`credentials`**: The necessary authentication credentials.

#### V1 (Old):

```python
# Initializing a Skyflow Client instance with a SkyflowConfiguration object
config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', token_provider)
client = Client(config)
```

#### V2 (New):

```python
# Initializing a Skyflow Client instance
client = (
    Skyflow.builder()
    .add_vault_config({
           'vault_id': '<VAULT_ID>', # Primary vault
           'cluster_id': '<CLUSTER_ID>', # ID from your vault URL e.g., https://{clusterId}.vault.skyflowapis.com
           'env': Env.PROD, # Env by default it is set to PROD
           'credentials': credentials # Individual credentials
    })
    .add_skyflow_credentials(credentials) # Skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.INFO) # set log level by default it is set to ERROR
    .build()
)
```

**Key Changes:**
- `vault_url` replaced with `cluster_Id`.
- Added environment specification (`env`).
- Instance-specific log levels.

### 3. Request & Response Structure

In V2, with the introduction of constructor parameters, you can now pass parameters to `InsertRequest`. This request need 
- **`table_name`**: The name of the table.
- **`values`**: An array of objects containing the data to be inserted.
The response will be of type `InsertResponse` class, which contains `inserted_fields` and errors.

#### V1 (Old): Request Building

```python
client.insert(
    {
        "records": [
            {
                "table": "cards",
                "fields": {
                    "cardNumber": "41111111111",
                    "cvv": "123",
                },
            }
        ]
    },
    InsertOptions(True),
)
```

#### V2 (New): Request Building

```python
# Prepare Insertion Data
insert_data = [
   {
       'card_number': '<VALUE1>',
       'cvv': '<VALUE2>',
   },
]

table_name = '<SENSITIVE_DATA_TABLE>' # Replace with your actual table name

# Create Insert Request
insert_request = InsertRequest(
   table_name=table_name,
   values=insert_data,
   return_tokens=True, # Optional: Get tokens for inserted data
   continue_on_error=True # Optional: Continue on partial errors
)

# Perform Secure Insertion
response = skyflow_client.vault(primary_vault_config.get('<VAULT_ID>')).insert(insert_request)
```

#### V1 (Old): Response Structure

```json
{
    "records": [
        {
            "table": "cards",
            "fields": {
                "cardNumber": "f3907186-e7e2-466f-91e5-48e12c2bcbc1",
                "cvv": "1989cb56-63da-4482-a2df-1f74cd0dd1a5",
                "skyflow_id": "d863633c-8c75-44fc-b2ed-2b58162d1117"
            },
            "request_index": 0
        }
    ]
}
```

#### V2 (New): Response Structure

```python
InsertResponse(
   inserted_fields=[
       {
           'skyflow_id': 'a8f3ed5d-55eb-4f32-bf7e-2dbf4b9d9097',
           'card_number': '5479-4229-4622-1393'
       }
   ],
   errors=[]
)
```

### 4. Request Options

In V2, we have introduced constructor parameters, allowing you to set options as key-value pairs as parameters in request.

#### V1 (Old):

```python
options = InsertOptions(
    tokens = True
)
```

#### V2 (New):

```python
insert_request = InsertRequest(
   table_name=table_name,
   values=insert_data,
   return_tokens=True, # Optional: Get tokens for inserted data
   continue_on_error=True # Optional: Continue on partial errors
)
```

### 5. Request Options

In V2, we have enriched the error details to provide better debugging capabilities. 
The error response now includes: 
- **http_status**: The HTTP status code. 
- **grpc_code**: The gRPC code associated with the error. 
- **details & message**: A detailed description of the error. 
- **request_id**: A unique request identifier for easier debugging.

#### V1 (Old) Error Structure:

```json
{
  "code": "<http_code>",
  "message": "<message>"
}
```

#### V2 (New) Error Structure:

```json
{
    "http_status": "<http_status>",
    "grpc_code": "<grpc_code>",
    "http_code": "<http_code>",
    "message": "<message>",
    "request_id": "<req_id>",
    "details": [ "<details>" ]
}
```

## Vault APIs

The vault python module is used to perform operations on the vault such as inserting records, detokenizing tokens, retrieving tokens for a skyflow_id and to invoke a connection.

To use this module, the skyflow client must first be initialized as follows.

```python
from skyflow import Env
from skyflow import Skyflow, LogLevel

# To generate Bearer Token from credentials string.
skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
credentials_string = json.dumps(skyflow_credentials)

# Pass one of api_key, token, credentials_string & path as credentials
credentials = {
        'token': 'BEARER_TOKEN', # bearer token
        # api_key: "API_KEY", # API_KEY
        # path: "PATH", # path to credentials file
        # credentials_string: credentials_string, #  credentials as string
}

client = (
    Skyflow.builder()
    .add_vault_config({
           'vault_id': 'VAULT_ID', # primary vault
           'cluster_id': 'CLUSTER_ID', # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           'env': Env.PROD, # Env by default it is set to PROD
           'credentials': credentials # individual credentials
    })
    .add_skyflow_credentials(credentials) # skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.INFO) # set log level by default it is set to ERROR
    .build()
)
```

Notes:

- If both Skyflow common credentials and individual credentials at the configuration level are provided, the individual credentials at the configuration level will take priority.

All Vault APIs must be invoked using a client instance.

### Insert data into the vault

To insert data into your vault, use the `insert` method. The `InsertRequest` class is used to create an insert request, which contains the values to be inserted in the form of a dictionary of records. Additionally, you can provide options in the insert request, such as returning tokenized data, upserting records, and continuing on error.

Insert call schema

```python
#Initialize Client
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

try:
    insert_data = [
        {'<FIELD_NAME1>': '<VALUE1>'},
        {'<FIELD_NAME2>': '<VALUE2>'}
    ]


    insert_request = InsertRequest(
        table_name = '<TABLE_NAME>',
        values = insert_data,
    )

    response = skyflow_client.vault('VAULT_ID').insert(insert_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

**Insert call [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/insert_records.py)**

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

try:
    insert_data = [
        {'card_number': '4111111111111111'},
    ]

    insert_request = InsertRequest(
        table_name = 'table1',
        values = insert_data,
        return_tokens = True  # returns tokens
    )

    response = client.vault('<VAULT_ID>').insert(insert_request)
    print("Response:", response)
except SkyflowError as e:
    print("Error Occurred:", e)

```

Skyflow returns tokens for the record you just inserted.

```python
InsertResponse(
    inserted_fields=
        [
            {
                'skyflow_id': 'a8f3ed5d-55eb-4f32-bf7e-2dbf4b9d9097',
                'card_number': '5479-4229-4622-1393'
            }
        ],
    errors=[]
)
```

**Insert call example with `continue_on_error` option**

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

try:
    insert_data = [
        {'card_number': '4111111111111111'},
        {'card_numbe': '4111111111111111'},  # Intentional typo card_numbe
    ]

    insert_request = InsertRequest(
        table_name = 'table1',
        values = insert_data,
        return_tokens = True,  # returns tokens
        continue_on_error = True
    )

    response = client.vault('<VAULT_ID>').insert(insert_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample Response

```python
InsertResponse(
    inserted_fields=
        [
            {
                'skyflow_id': '89c125d1-3bec-4360-b701-a032dda16500',
                'request_index': 0,
                'card_number': '5479-4229-4622-1393'
            }
        ],
    errors=
        [
          {
              'request_index': 1,
              'error': 'Insert failed. Column card_numbe is invalid. Specify a valid column.'
          }
        ]
)

```

**Insert call example with `upsert` options**

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

try:
    insert_data = [
        {"name": 'sample name'},
    ]

    insert_request = InsertRequest(
        table_name = 'table1',
        values = insert_data,
        return_tokens = True,  # returns tokens
        upsert = "name"  # unique column name
    )

    response = client.vault('<VAULT_ID>').insert(insert_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

Skyflow returns tokens, with `upsert` support, for the record you just inserted.

```python
InsertResponse(
    inserted_fields=
        [
            {
                'skyflow_id': 'a8f3ed5d-55eb-4f32-bf7e-2dbf4b9d9097',
                'name': '3f27b3d7-6bf0-432a-acf9-789c0470e2da'
            }
        ],
    errors=[]
)
```

### Detokenize

To retrieve tokens from your vault, you can use the `detokenize` method. The `DetokenizeRequest` class requires a list of detokenization data to be provided as input. Additionally, the redaction type and continue on error are optional parameters.

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['<TOKEN1>', '<TOKEN2>', '<TOKEN3>']

    detokenize_request = DetokenizeRequest(
        tokens =d etokenize_data,
        continue_on_error = False,  # optional
        redaction_type = RedactionType.PLAIN_TEXT  # optional
    )

    response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Notes:

- `redaction_type` defaults to `RedactionType.PLAIN_TEXT`.
- `continue_on_error` default valus is `False`.

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/detokenize_records.py) of a detokenize call:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-3840']

    detokenize_request = DetokenizeRequest(
        tokens = detokenize_data,
        continue_on_error = False,  # optional
        redaction_type = RedactionType.PLAIN_TEXT  # optional
    )

    response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample response:

```python
DetokenizeResponse(
    detokenized_fields=[
        {'token': '9738-1683-0486-1480', 'value': '4111111111111115', 'type': 'STRING'},
        {'token': '6184-6357-8409-6668', 'value': '4111111111111119', 'type': 'STRING'},
        {'token': '4914-9088-2814-3840', 'value': '4111111111111118', 'type': 'STRING'}
    ],
    errors=[]
)
```

An example of a detokenize call with continue_on_error:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-384']

    detokenize_request = DetokenizeRequest(
        tokens = detokenize_data,
        continue_on_error = True,  # optional
        redaction_type = RedactionType.PLAIN_TEXT  # optional
    )

    response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample response:

```python
DetokenizeResponse(
    detokenized_fields=[
        {
            'token': '9738-1683-0486-1480',
            'value': '4111111111111115',
            'type': 'STRING'
        },
        {
            'token': '6184-6357-8409-6668',
            'value': '4111111111111119',
            'type': 'STRING'
        }
    ],
    errors=[
        {
            'token': '4914-9088-2814-384',
            'error': 'Token Not Found'
        }
    ]
)

```

### Tokenize

To tokenize data, use the `tokenize` method. The `TokenizeRequest` class is utilized to create a tokenize request. In this request, you specify the `values` parameter, which is a list of dictionaries. Each dictionary contains two keys: `value` and `column_group`.

```python
from skyflow.vault.tokens import TokenizeRequest

tokenize_request = TokenizeRequest(
    values = [{
        'value': '<VALUE>',
        'column_group': '<COLUMN_GROUP>'
    }]
)
```

Sample usage

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/tokenize_records.py) of a tokenize call:

```python
from skyflow.error import SkyflowError
from skyflow.vault.tokens import TokenizeRequest

try:
    tokenize_request = TokenizeRequest(
        values = [{
            "value": '4111111111111111',
            "column_group": "card_number_cg"
        }]
    )

    response = client.vault('<VAULT_ID>').tokenize(tokenize_request)
    print(response)
except SyntaxError as e:
    print('Error Occurred: ', e)
```

Sample response:

```python
TokenizeResponse(
    tokenized_fields=[
        {
            'token': '5479-4229-4622-1393'
        }
    ]
)

```

### Get

To retrieve data using Skyflow IDs or unique column values, use the `get` method. The `GetRequest` class is used to create a get request, where you specify parameters such as the table name, redaction type, Skyflow IDs, column names, column values, and return tokens. If Skyflow IDs are provided, column names and column values cannot be used. Similarly, if column names or column values are provided, Skyflow IDs cannot be used.

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

GetRequest(
    table = '<TABLE_NAME>',
    ids = ['SKYFLOW_ID1>', 'SKYFLOW_ID2>'],
    return_tokens = True,
    redaction_type = RedactionType.PLAIN_TEXT
)

# or

GetRequest(
    table = '<TABLE_NAME>',
    column_name ='<COLUMN_NAME>',
    column_values = ['COLUMN_VALUE1>', 'COLUMN_VALUE2>'],
    redaction_type = RedactionType.PLAIN_TEXT
)
```

Sample usage

### Get By Column Name and Column Values

The following snippet shows how to use the `get` method using column names and column values. For details, see [get_column_values.py](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/get_column_values.py),

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

try:
    column_values = [
        '123456'
    ]

    get_request = GetRequest(
        table = 'table1',
        column_name = 'card_number', # It must be configured as unique in the schema.
        column_values = column_values,
        redaction_type = RedactionType.PLAIN_TEXT
    )

    response = skyflow_client.vault('<VAULT_ID>').get(get_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '123456',
            'skyflow_id': '4f7af9f9-09e0-4f47-af8e-04c9b1ee1968'
        }
    ],
    errors=[]
)

```

### Get By Skyflow Ids

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

GetRequest(
    table = '<TABLE_NAME>',
    ids = ['SKYFLOW_ID1>', 'SKYFLOW_ID2>'],
    return_tokens = True,
    redaction_type = RedactionType.PLAIN_TEXT
)
```

#### Redaction Types

There are 4 accepted values in Skyflow.RedactionTypes:

- `PLAIN_TEXT`
- `MASKED`
- `REDACTED`
- `DEFAULT`

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/get_records.py) of get by skyflow ids call:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

try:
    get_request = GetRequest(
        table = 'table1',
        ids = ['aea64577-12b1-4682-aad5-a183194c3f3d', 'b385c565-86eb-4af2-b959-8376f9b0754b'],
        redaction_type = RedactionType.PLAIN_TEXT
    )

    response = client.vault('<VAULT_ID>').get(get_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '4555555555555553',
            'skyflow_id': 'aea64577-12b1-4682-aad5-a183194c3f3d'
        },
        {
            'card_number': '4555555555555559',
            'skyflow_id': 'b385c565-86eb-4af2-b959-8376f9b0754b'
        }
    ],
    errors=[]
)

```

The following snippet shows how to use the `get()` method with return_tokens true.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import GetRequest

try:
    get_request = GetRequest(
        table = 'table1',
        ids = ['aea64577-12b1-4682-aad5-a183194c3f3d', 'b385c565-86eb-4af2-b959-8376f9b0754b'],
        return_tokens = True
    )

    response = client.vault('<VAULT_ID>').get(get_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '3562-0140-8820-7499',
            'skyflow_id': 'aea64577-12b1-4682-aad5-a183194c3f3d'
        },
        {
            'card_number': '3998-2139-0328-0697',
            'skyflow_id': 'b385c565-86eb-4af2-b959-8376f9b0754b'
        }
    ],
    errors=[]
)
```

### Update

To update data in your vault, use the `update` method. The `UpdateRequest` class is used to create an update request, where you specify parameters such as the table name, data (as a dictionary), tokens, return_tokens, and token_strict. If `return_tokens` is set to True, Skyflow returns tokens for the updated records. If `return_tokens` is set to False, Skyflow returns IDs for the updated records.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import UpdateRequest

try:
    update_data = {
        'skyflow_id': '<SKYFLOW_ID>',
        '<FIELD1>': '<VALUE1>'
    }

    update_request = UpdateRequest(
        table='TABLE_NAME',
        data=update_data
    )

    response = skyflow_client.vault('VAULT_ID').update(update_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

Sample usage

The following snippet shows how to use the `update()` method. For details, see [update_record.py](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/update_record.py),

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import UpdateRequest

try:
    update_data = {
        'skyflow_id': '3b80c76a-c0d7-4c02-be00-b4128cb0f315',
        'card_number': '4111111111117777'
    }

    update_request = UpdateRequest(
        table = 'table1',
        data = update_data
    )

    response = skyflow_client.vault('<VAULT_ID>').update(update_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

Sample response

`return_tokens` set to `True`

```python
UpdateResponse(
    updated_field={
        'skyflow_id': '3b80c76a-c0d7-4c02-be00-b4128cb0f315',
        'card_number': '4131-1751-0217-8491'
    },
    errors=[]
)

```

`return_tokens` set to `False`

```python
UpdateResponse(
    updated_field={'skyflow_id': '3b80c76a-c0d7-4c02-be00-b4128cb0f315'},
    errors=[]
)

```

### Delete

To delete records using Skyflow IDs, use the `delete` method. The `DeleteRequest` class accepts a list of Skyflow IDs that you want to delete, as shown below:

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import DeleteRequest

primary_delete_ids = [
    'SKYFLOW_ID1',
    'SKYFLOW_ID2',
    'SKYFLOW_ID3',
]

delete_request = DeleteRequest(
    table = '<TABLE_NAME>',
    ids = primary_delete_ids
)
```

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/delete_records.py) of delete call:

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import DeleteRequest

try:
    delete_ids = [
        '77e093f8-3ace-4295-8683-bb6745d6178e',
        'bf5989cc-79e8-4b2f-ad71-cb20b0a76091'
    ]

    delete_request = DeleteRequest(
        table='table1',
        ids=delete_ids
    )

    response = client.vault('<VAULT_ID>').delete(delete_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```

Sample response:

```python
DeleteResponse(
    deleted_ids=[
        '77e093f8-3ace-4295-8683-bb6745d6178e',
        'bf5989cc-79e8-4b2f-ad71-cb20b0a76091'
    ],
    errors=[]
)

```

### Invoke Connection

Using Skyflow Connection, end-user applications can integrate checkout/card issuance flow with their apps/systems. To invoke connection, use the `invoke` method of the Skyflow client.

```python
from skyflow.error import SkyflowError
from skyflow.vault.connection import InvokeConnectionRequest

body = {
    'KEY1': 'VALUE1',
    'KEY2': 'VALUE2'
}
headers = {
    'KEY1': 'VALUE1'
}
path_params = {
    'KEY1': 'VALUE1'
}
query_params = {
    'KEY1': 'VALUE1'
}

invoke_connection_request = InvokeConnectionRequest(
    method = Method.POST,
    body = body,
    headers = headers, # optional
    path_params = path_params, # optional
    query_params = query_params # optional
)
```

`methodName` supports the following methods:

- GET
- POST
- PUT
- PATCH
- DELETE

**path_params, query_params, request_header, request_body** are the JSON objects represented as dictionaries that will be sent through the connection integration url.

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/invoke_connection.py) of invoke_connection:

```python
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow.utils.enums import Method
from skyflow.error import SkyflowError
from skyflow.vault.connection import InvokeConnectionRequest

credentials = {
    'path': '/path/to/credentials.json',
}

client = (
    Skyflow.builder()
    .add_connection_config({
        'connection_id': '<CONNECTION_ID>',
        'connection_url': '<CONNECTION_URL>',
        'credentials': credentials
    })
    .set_log_level(LogLevel.OFF)
    .build()
)

invoke_connection_request = InvokeConnectionRequest(
    method=Method.POST,
    body={
        'card_number': '4337-1696-5866-0865',
        'ssn': '524-41-4248'
    },
    headers = {
        'Content-Type': 'application/json'
    }
)

response = client.connection('<CONNECTION_ID>').invoke(invoke_connection_request)

print(response)

```

Sample response:

```python
ConnectionResponse(
    {
        'card_number': '4337-1696-5866-0865',
        'ssn': '524-41-4248',
        'request_id': '84796a11-0b7d-4cb0-a348-cf9fefb5886f,84796a11-0b7d-4cb0-a348-cf9fefb5886f'
    }
)

```

### Query

To retrieve data with SQL queries, use the `query` method. `QueryRequest` is class that takes the `query` parameter as follows:

```python
from skyflow.vault.data import QueryRequest

query_request = QueryRequest(
    query= '<QUERY>'
)
```

See [Query your data](https://docs.skyflow.com/query-data/) and [Execute Query](https://docs.skyflow.com/record/#QueryService_ExecuteQuery) for guidelines and restrictions on supported SQL statements, operators, and keywords.

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/query_records.py) of Query call:

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import QueryRequest

query_request = QueryRequest(
    query = "SELECT * FROM cards WHERE skyflow_id='3ea3861-x107-40w8-la98-106sp08ea83f'"
)

try:
    skyflow_client.vault('<VAULT_ID>').query(query_request)
except SkyflowError as e:
    if e.data:
        print(e.data)
    else:
        print(e.message)
```

Sample Response

```python
QueryResponse(
    fields=[
        {
            'card_number': 'XXXXXXXXXXXX1112',
            'name': 'S***ar',
            'skyflow_id': '4f7af9f9-09e0-4f47-af8e-04c9b1ee1968',
            'tokenized_data': {}
        }
    ],
    errors=[]
)
```

## Logging

The skyflow python SDK provides useful logging using python's inbuilt `logging` library. By default the logging level of the SDK is set to `LogLevel.ERROR`. This can be changed by using `set_log_level(log_level)` as shown below:

```python
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env

# To generate Bearer Token from credentials string.
skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }
credentials_string = json.dumps(skyflow_credentials)

# Pass one of api_key, token, credentials_string & path as credentials
credentials = {
        'token': 'BEARER_TOKEN', # bearer token
        # api_key: "API_KEY", # API_KEY
        # path: "PATH", # path to credentials file
        # credentials_string: credentials_string, #  credentials as string
}

client = (
    Skyflow.builder()
    .add_vault_config({
           'vault_id': 'VAULT_ID', # primary vault
           'cluster_id': 'CLUSTER_ID', # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           'env': Env.PROD, # Env by default it is set to PROD
           'credentials': credentials # individual credentials
    })
    .add_skyflow_credentials(credentials) # skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.INFO) # set log level by default it is set to ERROR
    .build()
)
```

Current the following 5 log levels are supported:

- `DEBUG`:

  When `LogLevel.DEBUG` is passed, all level of logs will be printed(DEBUG, INFO, WARN, ERROR)

- `INFO`:

  When `LogLevel.INFO` is passed, INFO logs for every event that has occurred during the SDK flow execution will be printed along with WARN and ERROR logs

- `WARN`:

  When `LogLevel.WARN` is passed, WARN and ERROR logs will be printed

- `ERROR`:

  When `LogLevel.ERROR` is passed, only ERROR logs will be printed.

- `OFF`:

  `LogLevel.OFF` can be used to turn off all logging from the Skyflow SDK.

`Note`: The ranking of logging levels is as follows : `DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`

## Reporting a Vulnerability

If you discover a potential security issue in this project, please reach out to us at security@skyflow.com. Please do not create public GitHub issues or Pull Requests, as malicious actors could potentially view them.
