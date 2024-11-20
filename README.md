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
  - [Vault APIs](#vault-apis)
    - [Insert data into the vault](#insert-data-into-the-vault)
    - [Detokenize](#detokenize)
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
        table_name='<TABLE_NAME>',
        values=insert_data,
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
        table_name='table1',
        values=insert_data,
        return_tokens=True  # returns tokens
    )

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').insert(insert_request)
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
    error=[]
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
        table_name='table1',
        values=insert_data,
        return_tokens=True,  # returns tokens
        continue_on_error=True
    )

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').insert(insert_request)
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
    error=
        [
          {
              'request_index': 1,
               'error': 'Insert failed. Column card_numbe is invalid. Specify a valid column.'}
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
        table_name='table1',
        values=insert_data,
        return_tokens=True,  # returns tokens
        upsert="name"  # unique column name
    )

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').insert(insert_request)
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
    error=[]
)
```

### Detokenize

To retrieve tokens from your vault, you can use the `detokenize` method. The `DetokenizeRequest` class requires a list of detokenization data to be provided as input. Additionally, the redaction type and continue on error are optional parameters.

```python
from skyflow.error import SkyflowError
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['<TOKEN1>', '<TOKEN2>', '<TOKEN3>']

    detokenize_request = DetokenizeRequest(
        tokens=detokenize_data,
        continue_on_error=False,  # optional
        redaction_type='plain-text'  # optional
    )

    response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)

```
Notes:
- `redaction` defaults to `plain-text`.
- `continue_on_error` default valus is `False`.

An [example](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/detokenize_records.py) of a detokenize call:

```python
from skyflow.error import SkyflowError
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-3840']

    detokenize_request = DetokenizeRequest(
        tokens=detokenize_data,
        continue_on_error=False,  # optional
        redaction_type='plain-text'  # optional
    )

    response = skyflow_client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').detokenize(detokenize_request)
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
from skyflow.vault.tokens import DetokenizeRequest

try:
    detokenize_data = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-384']

    detokenize_request = DetokenizeRequest(
        tokens=detokenize_data,
        continue_on_error=True,  # optional
        redaction_type='plain-text'  # optional
    )

    response = skyflow_client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').detokenize(detokenize_request)
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

To tokenize data, use the `tokenize` method. The `TokenizeRequest` class is utilized to create a tokenize request. In this request, you specify the `tokenize_parameters` parameter, which is a list of dictionaries. Each dictionary contains two keys: `value` and `column_group`.

```python
from skyflow.vault.tokens import TokenizeRequest

tokenize_request = TokenizeRequest(
    tokenize_parameters=[{
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
        tokenize_parameters=[{
            "value": '4111111111111111',
            "column_group": "card_number_cg"
        }]
    )

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').tokenize(tokenize_request)
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
from skyflow.vault.data import GetRequest

GetRequest(
    table = '<TABLE_NAME>',
    ids = ['SKYFLOW_ID1>', 'SKYFLOW_ID2>'],
    return_tokens = True,
    redaction_type='plain-text'
)

# or

GetRequest(
    table = '<TABLE_NAME>',
    column_name='<COLUMN_NAME>',
    column_values=['COLUMN_VALUE1>', 'COLUMN_VALUE2>'],
    redaction_type='plain-text'
)
```
Sample usage

### Get By Column Name and Column Values

The following snippet shows how to use the `get` method using column names and column values. For details, see [get_column_values.py](https://github.com/skyflowapi/skyflow-python/blob/SK-1749-readme/samples/vault_api/get_column_values.py),

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import GetRequest

try:
    column_values = [
        '123456'
    ]

    get_request = GetRequest(
        table='table1',
        column_name="card_number", # It must be configured as unique in the schema. 
        column_values=column_values,
        redaction_type='plain-text'
    )

    response = skyflow_client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').get(get_request)
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
    error=[]
)

```

### Get By Skyflow Ids

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import GetRequest

GetRequest(
    table = '<TABLE_NAME>',
    ids = ['SKYFLOW_ID1>', 'SKYFLOW_ID2>'],
    return_tokens = True,
    redaction_type='plain-text'
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
from skyflow.vault.data import GetRequest

try:
    get_request = GetRequest(
        table='table1',
        ids=['aea64577-12b1-4682-aad5-a183194c3f3d', 'b385c565-86eb-4af2-b959-8376f9b0754b'],
        redaction_type="plain-text"
    )

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').get(get_request)
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
    error=[]
)

```


The following snippet shows how to use the `get()` method with return_tokens true.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import GetRequest

try:
    get_request = GetRequest(
        table='table1',
        ids=['aea64577-12b1-4682-aad5-a183194c3f3d', 'b385c565-86eb-4af2-b959-8376f9b0754b'],
        return_tokens=True
    )
    
    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').get(get_request)
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
    error=[]
)
```

### Update

To update data in your vault, use the `update` method. The `UpdateRequest` class is used to create an update request, where you specify parameters such as the table name, data (as a dictionary), tokens, return_tokens, and token_strict. If `return_tokens` is set to True, Skyflow returns tokens for the updated records. If `return_tokens` is set to False, Skyflow returns IDs for the updated records.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import UpdateRequest

try:
    update_data = {
        'id': '<SKYFLOW_ID>',
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
        'id': '3b80c76a-c0d7-4c02-be00-b4128cb0f315',
        'card_number': '4111111111117777'
    }

    update_request = UpdateRequest(
        table='table1',
        data=update_data
    )

    response = skyflow_client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').update(update_request)
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
    error=[]
)

```

`return_tokens` set to `False`

```python
UpdateResponse(
    updated_field={'skyflow_id': '3b80c76a-c0d7-4c02-be00-b4128cb0f315'},
    error=[]
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
    table='<TABLE_NAME>',
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

    response = client.vault('d3dd9bbb7abc4c779b72f32cb7ee5d14').delete(delete_request)
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
    error=[]
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
    method=Method.POST,
    body=body,
    request_headers = headers, # optional
    path_params = path_params, # optional
    query_params=query_params # optional
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
    request_headers = {
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

queryInput = {
	query: "SELECT * FROM cards WHERE skyflow_id='3ea3861-x107-40w8-la98-106sp08ea83f'"
}

try:
    client.query(queryInput)
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
            "fields": {
                "card_number": "XXXXXXXXXXXX1111",
                "card_pin": "*REDACTED*",
                "cvv": "",
                "expiration_date": "*REDACTED*",
                "expiration_month": "*REDACTED*",
                "expiration_year": "*REDACTED*",
                "name": "a***te",
                "skyflow_id": "3ea3861-x107-40w8-la98-106sp08ea83f",
                "ssn": "XXX-XX-6789",
                "zip_code": None
            },
        }
    ],
    error=[]
)
```

## Logging

The skyflow python SDK provides useful logging using python's inbuilt `logging` library. By default the logging level of the SDK is set to `LogLevel.ERROR`. This can be changed by using `set_log_level(log_level)` as shown below:

```python
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env

client = (
    Skyflow.builder()
    .add_vault_config({
           'vault_id': 'VAULT_ID', # primary vault
           'cluster_id': 'CLUSTER_ID', # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           'env': Env.PROD, # Env by default it is set to PROD
           'credentials': "<CREDENTIALS>" # individual credentials
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
