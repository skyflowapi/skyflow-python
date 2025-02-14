# Skyflow Python

The Skyflow Python SDK is designed to help with integrating Skyflow into a Python backend.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [Install](#installation)
    - [Requirements](#requirements)
    - [Configuration](#configuration)
- [Migration from v1 to v2](#migration-from-v1-to-v2)
    - [Authentication options](#1-authentication-options)
    - [Initializing the client](#2-initializing-the-client)
    - [Request & response structure](#3-request--response-structure)
    - [Request options](#4-request-options)
    - [Error structure](#5-error-structure)
- [Quickstart](#quickstart)
    - [Authenticate](#authenticate)
    - [Initialize the client](#initialize-the-client)
    - [Insert data into the vault](#insert-data-into-the-vault)
  - [Vault](#vault-apis)
    - [Insert data into the vault](#insert-data-into-the-vault)
    - [Detokenize](#detokenize)
    - [Tokenize](#tokenize)
    - [Get](#get)
        - [Get by skyflow IDs](#get-by-skyflow-ids)
        - [Get tokens](#get-tokens)
        - [Get by column name and column values](#get-by-column-name-and-column-values)
        - [Redaction types](#redaction-types)
    - [Update](#update)
    - [Delete](#delete)
    - [Invoke Connection](#invoke-connection)
    - [Query](#query)
  - [Logging](#logging)
  - [Reporting a Vulnerability](#reporting-a-vulnerability)

## Overview

- Authenticate using a Skyflow service account and generate bearer tokens for secure access.

- Perform Vault API operations such as inserting, retrieving, and tokenizing sensitive data with ease.

- Invoke connections to third-party APIs without directly handling sensitive data, ensuring compliance and data protection.


## Installation

### Requirements

- Python 3.8.0 and above (tested with Python 3.8.0)

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
## Migration from V1 to V2

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

#### V1 (Old): Passing the token provider function below as a parameter to the Configuration.

```python
# User defined function to provide access token to the vault apis
def token_provider():
    global bearerToken
    if !(is_expired(bearerToken)):
        return bearerToken
    bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken
```

#### V2 (New): Passing one of the following:

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

### 2. Initializing the client

In V2, we have introduced a Builder design pattern for client initialization and added support for multi-vault. This allows you to configure multiple vaults during client initialization. 

In V2, the log level is tied to each individual client instance. 

During client initialization, you can pass the following parameters:

- **`vault_id`** and **`cluster_id`**: These values are derived from the vault ID & vault URL.
- **`env`**: Specify the environment (e.g., SANDBOX or PROD).
- **`credentials`**: The necessary authentication credentials.

#### V1 (Old):

```python
# Initializing a Skyflow Client instance with a SkyflowConfiguration object
config = Configuration('<VAULT_ID>', '<VAULT_URL>', token_provider)
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
   table_name=table_name,        # Replace with the table name
   values=insert_data,
   return_tokens=False,          # Do not return tokens
   continue_on_error=False,      # Stop inserting if any record fails
   upsert='<UPSERT_COLUMN>',     # Replace with the column name used for upsert logic
   token_mode=TokenMode.DISABLE, # Disable BYOT
   tokens='<TOKENS>'             # Replace with tokens when TokenMode is ENABLE.
)
```

### 5. Error Structure

In V2, we have enriched the error details to provide better debugging capabilities. 
The error response now includes: 
- **http_status**: The HTTP status code. 
- **grpc_code**: The gRPC code associated with the error. 
- **details** & **message**: A detailed description of the error. 
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
    "request_id": "<request_id>",
    "details": [ "<details>" ]
}
```

## Quickstart
Get started quickly with the essential steps: authenticate, initialize the client, and perform a basic vault operation. This section provides a minimal setup to help you integrate the SDK efficiently.

### Authenticate
You can use an API key to authenticate and authorize requests to an API. For authenticating via bearer tokens and different supported bearer token types, refer to the Authenticate with bearer tokens section. 

```python
# create a new credentials dictionary
credentials = {
        api_key: "<API_KEY>", # add your API key in credentials
}
```

### Initialize the client
To get started, you must first initialize the skyflow client. While initializing the skyflow client, you can specify different types of credentials.
**1. API keys**
- A unique identifier used to authenticate and authorize requests to an API.
**2. Bearer tokens**
- A temporary access token used to authenticate API requests, typically included in the
Authorization header.
**3. Service account credentials file path**
- The file path pointing to a JSON file containing credentials for a service account, used
for secure API access.
**4. Service account credentials string**
- A JSON-formatted string containing service account credentials, often used as an alternative to a file for programmatic authentication.

Note: Only one type of credential can be used at a time.

```python
import json
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env

"""
Example program to initialize the Skyflow client with various configurations.
The Skyflow client facilitates secure interactions with the Skyflow vault, 
such as securely managing sensitive data.
"""

# Step 1: Define the primary credentials for authentication.
# Note: Only one type of credential can be used at a time. You can choose between:
# - API key
# - Bearer token
# - A credentials string (JSON-formatted)
# - A file path to a credentials file.

# Initialize primary credentials using a Bearer token for authentication.
primary_credentials = {
    'token': '<BEARER_TOKEN>'  # Replace <BEARER_TOKEN> with your actual authentication token.
}

# Step 2: Configure the primary vault details.
# VaultConfig stores all necessary details to connect to a specific Skyflow vault.
primary_vault_config = {
    'vault_id': '<PRIMARY_VAULT_ID>',  # Replace with your primary vault's ID.
    'cluster_id': '<CLUSTER_ID>',      # Replace with the cluster ID (part of the vault URL, e.g., https://{clusterId}.vault.skyflowapis.com).
    'env': Env.PROD,                    # Set the environment (PROD, SANDBOX, STAGE, DEV).
    'credentials': primary_credentials  # Attach the primary credentials to this vault configuration.
}

# Step 3: Create credentials as a JSON object (if a Bearer Token is not provided).
# Demonstrates an alternate approach to authenticate with Skyflow using a credentials object.
skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',       # Replace with your Client ID.
    'clientName': '<YOUR_CLIENT_NAME>',   # Replace with your Client Name.
    'tokenURI': '<YOUR_TOKEN_URI>',       # Replace with the Token URI.
    'keyID': '<YOUR_KEY_ID>',             # Replace with your Key ID.
    'privateKey': '<YOUR_PRIVATE_KEY>'    # Replace with your Private Key.
}

# Step 4: Convert the JSON object to a string and use it as credentials.
# This approach allows the use of dynamically generated or pre-configured credentials.
credentials_string = json.dumps(skyflow_credentials)  # Converts JSON object to string for use as credentials.

# Step 5: Define secondary credentials (API key-based authentication as an example).
# Demonstrates a different type of authentication mechanism for Skyflow vaults.
secondary_credentials = {
    'token': '<BEARER_TOKEN>'  # Replace with your API Key for authentication.
}

# Step 6: Configure the secondary vault details.
# A secondary vault configuration can be used for operations involving multiple vaults.
secondary_vault_config = {
    'vault_id': '<SECONDARY_VAULT_ID>',  # Replace with your secondary vault's ID.
    'cluster_id': '<CLUSTER_ID>',        # Replace with the corresponding cluster ID.
    'env': Env.PROD,                      # Set the environment for this vault.
    'credentials': secondary_credentials  # Attach the secondary credentials to this configuration.
}

# Step 7: Define tertiary credentials using a path to a credentials JSON file.
# This method demonstrates an alternative authentication method.
tertiary_credentials = {
    'token': '<BEARER_TOKEN>'  # Replace with the path to your credentials file.
}

# Step 8: Configure the tertiary vault details.
tertiary_vault_config = {
    'vault_id': '<TERTIARY_VAULT_ID>',   # Replace with the tertiary vault ID.
    'cluster_id': '<CLUSTER_ID>',        # Replace with the corresponding cluster ID.
    'env': Env.PROD,                      # Set the environment for this vault.
    'credentials': tertiary_credentials  # Attach the tertiary credentials.
}

# Step 9: Build and initialize the Skyflow client.
# Skyflow client is configured with multiple vaults and credentials.
skyflow_client = (
    Skyflow.builder()
    .add_vault_config(primary_vault_config)   # Add the primary vault configuration.
    .add_vault_config(secondary_vault_config) # Add the secondary vault configuration.
    .add_vault_config(tertiary_vault_config)  # Add the tertiary vault configuration.
    .add_skyflow_credentials(skyflow_credentials)  # Add JSON-formatted credentials if applicable.
    .set_log_level(LogLevel.ERROR)  # Set log level for debugging or monitoring purposes.
    .build()
)

# The Skyflow client is now fully initialized.
# Use the `skyflow_client` object to perform secure operations such as:
# - Inserting data
# - Retrieving data
# - Deleting data
# within the configured Skyflow vaults.

```
Notes
- If both Skyflow common credentials and individual credentials at the configuration level are specified, the individual credentials at the configuration level will take precedence.
- If neither Skyflow common credentials nor individual configuration-level credentials are provided, the SDK attempts to retrieve credentials from the SKYFLOW_CREDENTIALS environment variable.
- All Vault operations require a client instance.

### Insert data into the vault
To insert data into your vault, use the `insert` method.  The `InsertRequest` class creates an insert request, which includes the values to be inserted as a list of records. Below is a simple example to get started. For advanced options, check out Insert data into the vault section.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

"""
 * This example demonstrates how to insert sensitive data (e.g., card information) into a Skyflow vault using the Skyflow client.
 *
 * 1. Initializes the Skyflow client.
 * 2. Prepares a record with sensitive data (e.g., card number and cardholder name).
 * 3. Creates an insert request for inserting the data into the Skyflow vault.
 * 4. Prints the response of the insert operation.
"""

try:
    # Step 1: Initialize data to be inserted into the Skyflow vault
    insert_data = [
        {
            'card_number': '4111111111111111',  # Replace with actual card number (sensitive data)
            'cardholder_name': 'John Doe',     # Replace with actual cardholder name (sensitive data)
        },
    ]

    # Step 2: Create Insert Request
    insert_request = InsertRequest(
        table_name='table1',  # Specify the table in the vault where the data will be inserted
        values=insert_data,   # Attach the data (records) to be inserted
        return_tokens=True,   # Specify if tokens should be returned upon successful insertion
        continue_on_error=True  # Optional: Continue on partial errors
    )

    # Step 3: Perform the insert operation using the Skyflow client
    insert_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').insert(insert_request)
    # Replace the vault ID "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 4: Print the response from the insert operation
    print('Insert Response: ', insert_response)

except SkyflowError as error:
    # Step 5: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```
Skyflow returns tokens for the record that was just inserted.

```python
InsertResponse(
    inserted_fields=
        [
            {
                'skyflow_id': 'a8f3ed5d-55eb-4f32-bf7e-2dbf4b9d9097',
                'card_number': '5484-7829-1702-9110',
                'cardholder_name': 'b2308e2a-c1f5-469b-97b7-1f193159399b'
            }
        ],
    errors=[]
)
```


## Vault

The Vault module performs operations on the vault, including inserting records, detokenizing tokens, and retrieving tokens associated with a skyflow_id.


### Insert data into the vault

Apart from using the `insert` method to insert data into your vault covered in Quickstart, you can also specify options in `InsertRequest`, such as returning tokenized data, upserting records, or continuing the operation in case of errors.

#### Construct an insert request

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

"""
Example program to demonstrate inserting data into a Skyflow vault, along with corresponding InsertRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Prepare the data to be inserted into the Skyflow vault
    insert_data = [
        # Create the first record with field names and their respective values
        {
            '<FIELD_NAME_1>': '<VALUE_1>',  # Replace with actual field name and value
            '<FIELD_NAME_2>': '<VALUE_2>',  # Replace with actual field name and value
        },
        # Create the second record with field names and their respective values
        {
            '<FIELD_NAME_1>': '<VALUE_1>',  # Replace with actual field name and value
            '<FIELD_NAME_2>': '<VALUE_2>',  # Replace with actual field name and value
        }
    ]

    # Step 2: Build an InsertRequest object with the table name and the data to insert
    insert_request = InsertRequest(
        table_name='<TABLE_NAME>',  # Replace with the actual table name in your Skyflow vault
        values=insert_data,         # Attach the data to be inserted
    )

    # Step 3: Use the Skyflow client to perform the insert operation
    insert_response = skyflow_client.vault('<VAULT_ID>').insert(insert_request)
    # Replace <VAULT_ID> with your actual vault ID

    # Print the response from the insert operation
    print('Insert Response: ', insert_response)

# Step 5: Handle any exceptions that occur during the insert operation
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

#### Insert call example with `continue_on_error` option
The `continue_on_error` flag is a boolean that determines whether insert operation should proceed despite encountering partial errors. Set to `True` to allow the process to continue even if some errors occur.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

"""
This example demonstrates how to insert sensitive data (e.g., card information) into a Skyflow vault using the Skyflow client.

1. Initializes the Skyflow client.
2. Prepares a record with sensitive data (e.g., card number and cardholder name).
3. Creates an insert request for inserting the data into the Skyflow vault.
4. Specifies options to continue on error and return tokens.
5. Prints the response of the insert operation.
"""

try:
    # Initialize Skyflow client
    # Step 1: Initialize a list to hold the data records to be inserted into the vault
    insert_data = [
        # Step 2: Create the first record with card number and cardholder name
        {
            'card_number': '4111111111111111',  # Replace with actual card number (sensitive data)
            'cardholder_name': 'John Doe',     # Replace with actual cardholder name (sensitive data)
        },
        # Step 3: Create the second record with card number and cardholder name
        {
            'card_number': '4111111111111111',  # Ensure field name matches ("card_number")
            'cardholder_name': 'Jane Doe',     # Replace with actual cardholder name (sensitive data)
        }
    ]

    # Step 4: Build the InsertRequest object with the data records to insert
    insert_request = InsertRequest(
        table_name='table1',  # Specify the table in the vault where the data will be inserted
        values=insert_data,   # Attach the data (records) to be inserted
        return_tokens=True,   # Specify if tokens should be returned upon successful insertion
        continue_on_error=True  # Specify to continue inserting records even if an error occurs for some records
    )

    # Step 5: Perform the insert operation using the Skyflow client
    insert_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').insert(insert_request)
    # Replace the vault ID "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 6: Print the response from the insert operation
    print('Insert Response: ', insert_response)

except SkyflowError as error:
    # Step 7: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample Response

```python
InsertResponse(
    inserted_fields=
        [
            {
                'card_number': '5484-7829-1702-9110',
                'request_index': 0,
                'skyflow_id': '9fac9201-7b8a-4446-93f8-5244e1213bd1',
                'cardholder_name': 'b2308e2a-c1f5-469b-97b7-1f193159399b',

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

**Insert call example with `upsert` option**
An upsert operation checks for a record based on a unique column's value. If a match exists, the record is updated; otherwise, a new record is inserted.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import InsertRequest

"""
This example demonstrates how to insert sensitive data (e.g., card information) into a Skyflow vault using the Skyflow client.

1. Initializes the Skyflow client.
2. Prepares a record with sensitive data (e.g., card number and cardholder name).
3. Creates an insert request for inserting the data into the Skyflow vault.
4. Specifies the field (cardholder_name) for upsert operations.
5. Prints the response of the insert operation.
"""

try:
    # Initialize Skyflow client
    # Step 1: Initialize a list to hold the data records for the insert/upsert operation
    insert_data = [
        # Step 2: Create a record with the field 'cardholder_name' to insert or upsert
        {
            'cardholder_name': 'John Doe',     # Replace with the actual cardholder name
        }
    ]

    # Step 3: Build the InsertRequest object with the upsertData
    insert_request = InsertRequest(
        table_name='table1',      # Specify the table in the vault where the data will be inserted
        values=insert_data,       # Attach the data (records) to be inserted
        return_tokens=True,       # Specify if tokens should be returned upon successful insertion
        upsert='cardholder_name'  # Specify the field to be used for upsert operations (e.g., cardholder_name)
    )

    # Step 4: Perform the insert/upsert operation using the Skyflow client
    insert_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').insert(insert_request)
    # Replace the vault ID "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 5: Print the response from the insert/upsert operation
    print('Insert Response: ', insert_response)

except SkyflowError as error:
    # Step 6: Handle any exceptions that may occur during the insert/upsert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Skyflow returns tokens, with `upsert` support, for the record you just inserted.

```python
InsertResponse(
    inserted_fields=
        [
            {
                'skyflow_id': '9fac9201-7b8a-4446-93f8-5244e1213bd1',
                'name': '73ce45ce-20fd-490e-9310-c1d4f603ee83'
            }
        ],
    errors=[]
)
```

### Detokenize

To retrieve tokens from your vault, use the `detokenize` method. The `DetokenizeRequest` class requires a list of detokenization data as input. Additionally, you can provide optional parameters, such as the redaction type and the option to continue on error.
#### Construct a detokenize request
```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest
"""
This example demonstrates how to detokenize sensitive data from tokens stored in a Skyflow vault, along with corresponding DetokenizeRequest schema. 
"""
try:
    # Initialize Skyflow client
    # Step 1: Step 1: Initialize a list of tokens to be detokenized (replace with actual tokens)
    detokenize_data = ['<YOUR_TOKEN_VALUE_1>', '<YOUR_TOKEN_VALUE_2>', '<YOUR_TOKEN_VALUE_3>']  # Replace with your actual token values

    # Step 2: Create the DetokenizeRequest object with the tokens and redaction type
    detokenize_request = DetokenizeRequest(
        tokens=detokenize_data,                  # Provide the list of tokens to be detokenized
        continue_on_error=True,                  # Continue even if one token cannot be detokenized
        redaction_type=RedactionType.PLAIN_TEXT  # Specify how the detokenized data should be returned (plain text)
    )

    # Step 3: Call the Skyflow vault to detokenize the provided tokens
    detokenize_response = skyflow_client.vault('<VAULT_ID>').detokenize(detokenize_request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID

    # Step 4: Print the detokenization response, which contains the detokenized data
    print('Response:', detokenize_response)
# Step 5: Handle any errors that occur during the detokenization process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the exception for debugging purposes
```

Notes:

- `redaction_type` defaults to `RedactionType.PLAIN_TEXT`.
- `continue_on_error` default valus is `False`.

An example of a detokenize cal

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest
"""
This example demonstrates how to detokenize sensitive data from tokens stored in a Skyflow vault.

1. Initializes the Skyflow client.
2. Creates a list of tokens (e.g., credit card tokens) that represent the sensitive data.
3. Builds a detokenization request using the provided tokens and specifies how the redacted data should be returned.
4. Calls the Skyflow vault to detokenize the tokens and retrieves the detokenized data.
5. Prints the detokenization response, which contains the detokenized values or errors.
"""
try:
    # Initialize Skyflow client
    # Step 1: Step 1: Initialize a list of tokens to be detokenized (replace with actual tokens)
    tokens = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-3840']  # Replace with your actual token values

    # Step 2: Create the DetokenizeRequest object with the tokens and redaction type
    detokenize_request = DetokenizeRequest(
        tokens=tokens,                           # Provide the list of tokens to be detokenized
        continue_on_error=False,                 # Stop the process if any token cannot be detokenized
        redaction_type=RedactionType.PLAIN_TEXT  # Specify how the detokenized data should be returned (plain text)
    )

    # Step 3: Call the Skyflow vault to detokenize the provided tokens
    detokenize_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').detokenize(detokenize_request)
    # Replace "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 4: Print the detokenization response, which contains the detokenized data
    print('Response:', detokenize_response)
# Step 5: Handle any errors that occur during the detokenization process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the exception for debugging purposes
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

An example of a detokenize call with `continue_on_error` option:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest
"""
This example demonstrates how to detokenize sensitive data from tokens stored in a Skyflow vault.

1. Initializes the Skyflow client.
2. Creates a list of tokens (e.g., credit card tokens) that represent the sensitive data.
3. Builds a detokenization request using the provided tokens and specifies how the redacted data should be returned.
4. Calls the Skyflow vault to detokenize the tokens and retrieves the detokenized data.
5. Prints the detokenization response, which contains the detokenized values or errors.
"""
try:
    # Initialize Skyflow client
    # Step 1: Step 1: Initialize a list of tokens to be detokenized (replace with actual tokens)
    tokens = ['9738-1683-0486-1480', '6184-6357-8409-6668', '4914-9088-2814-3840']  # Replace with your actual token values

    # Step 2: Create the DetokenizeRequest object with the tokens and redaction type
    detokenize_request = DetokenizeRequest(
        tokens=tokens,                           # Provide the list of tokens to be detokenized
        continue_on_error=True,                  # Continue even if some tokens cannot be detokenized
        redaction_type=RedactionType.PLAIN_TEXT  # Specify how the detokenized data should be returned (plain text)
    )

    # Step 3: Call the Skyflow vault to detokenize the provided tokens
    detokenize_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').detokenize(detokenize_request)
    # Replace "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 4: Print the detokenization response, which contains the detokenized data
    print('Response:', detokenize_response)
# Step 5: Handle any errors that occur during the detokenization process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the exception for debugging purposes
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

Tokenization replaces sensitive data with unique identifier tokens. This approach protects sensitive information by securely storing the original data while allowing the use of tokens within your application.

To tokenize data, use the `tokenize` method. The `TokenizeRequest` class creates a tokenize request. In this request, you specify the values parameter, which is a list of column values objects. Each column value contains two properties: `value` and `column_group`.

#### Construct a tokenize request

```python
from skyflow.error import SkyflowError
from skyflow.vault.tokens import TokenizeRequest

"""
This example demonstrates how to tokenize sensitive data (e.g., credit card information) using the Skyflow client, along with corresponding TokenizeRequest schema.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of column values to be tokenized (replace with actual sensitive data)
    column_values = [
        # Step 2: Create column values for each sensitive data field (e.g., card number and cardholder name)
        {"value": "<VALUE_1>", "column_group": "<COLUMN_GROUP_1>"}, # Replace <VALUE_1> and <COLUMN_GROUP_1> with actual data
        {"value": "<VALUE_2>", "column_group": "<COLUMN_GROUP_2>"}  # Replace <VALUE_2> and <COLUMN_GROUP_2> with actual data
    ]

    # Step 3: Build the TokenizeRequest with the column values
    tokenize_request = TokenizeRequest(
        values=column_values
    )

    # Step 4: Call the Skyflow vault to tokenize the sensitive data
    tokenize_response = skyflow_client.vault('<VAULT_ID>').tokenize(tokenize_request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID

    # Step 5: Print the tokenization response, which contains the generated tokens or errors
    print(tokenize_response)

# Step 6: Handle any errors that occur during the tokenization process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

An example of Tokenize call

```python
from skyflow.error import SkyflowError
from skyflow.vault.tokens import TokenizeRequest

"""
This example demonstrates how to tokenize sensitive data (e.g., credit card information) using the Skyflow client.

1. Initializes the Skyflow client.
2. Creates a column value for sensitive data (e.g., credit card number).
3. Builds a tokenize request with the column value to be tokenized.
4. Sends the request to the Skyflow vault for tokenization.
5. Prints the tokenization response, which includes the token or errors.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of column values to be tokenized (replace with actual sensitive data)
    column_values = [
        # Step 2: Create column values for each sensitive data field (e.g., card number and cardholder name)
        {"value": "4111111111111111", "column_group": "card_number_cg"}, # Replace <VALUE_1> and <COLUMN_GROUP_1> with actual data
    ]

    # Step 3: Build the TokenizeRequest with the column values
    tokenize_request = TokenizeRequest(
        values=column_values
    )

    # Step 4: Call the Skyflow vault to tokenize the sensitive data
    tokenize_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').tokenize(tokenize_request)
    # Replace "9f27764a10f7946fe56b3258e117" with your actual Skyflow vault ID

    # Step 5: Print the tokenization response, which contains the generated tokens or errors
    print(tokenize_response)

# Step 6: Handle any errors that occur during the tokenization process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes

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

To retrieve data using Skyflow IDs or unique column values, use the get method. The `GetRequest` class creates a get request, where you specify parameters such as the table name, redaction type, Skyflow IDs, column names, column values, and whether to return tokens. If you specify Skyflow IDs, you can't use column names and column values, and the inverse is true—if you specify column names and column values, you can't use Skyflow IDs.

#### Construct a get request

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

"""
This example demonstrates how to retrieve data from the Skyflow vault using different methods, along with corresponding GetRequest schema.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of Skyflow IDs to retrieve records (replace with actual Skyflow IDs)
    ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>']  # Replace with actual Skyflow IDs

    # Step 2: Create a GetRequest to retrieve records by Skyflow ID without returning tokens
    get_by_id_request = GetRequest(
        table='<TABLE_NAME>',  # Replace with your actual table name
        ids=ids,
        return_tokens=False,   # Set to false to avoid returning tokens
        redaction_type=RedactionType.PLAIN_TEXT # Redact data as plain text
    )

    # Send the request to the Skyflow vault and retrieve the records
    get_by_id_response = skyflow_client.vault('<VAULT_ID>').get(get_by_id_request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID

    print(get_by_id_response)

    # Step 3: Create another GetRequest to retrieve records by Skyflow ID with tokenized values
    get_tokens_request = GetRequest(
        table='<TABLE_NAME>',  # Replace with your actual table name
        ids=ids,
        return_tokens=True  # Set to True to return tokenized values
    )

    # Send the request to the Skyflow vault and retrieve the tokenized records
    get_tokens_response = skyflow_client.vault('<VAULT_ID>').get(get_tokens_request)
    print(get_tokens_response)

    column_values = [
        '<COLUMN_VALUE_1>',  # Replace with the actual column value
        '<COLUMN_VALUE_2>'   # Replace with the actual column value
    ]

    # Step 4: Create a GetRequest to retrieve records based on specific column values
    get_by_column_request = GetRequest(
        table='<TABLE_NAME>',  # Replace with the actual table name
        column_name='<COLUMN_NAME>',  # Replace with the column name
        column_values=column_values,  # Add the list of column values to filter by
        redaction_type=RedactionType.PLAIN_TEXT  # Redact data as plain text
    )

    # Send the request to the Skyflow vault and retrieve the filtered records
    get_by_column_response = skyflow_client.vault('<VAULT_ID>').get(get_by_column_request)
    print(get_by_column_response)
# Step 5: Handle any errors that occur during the retrieval process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes

```

#### Get by skyflow IDs
Retrieve specific records using skyflow `ids`. Ideal for fetching exact records when IDs are known.


An example of a get call to retrieve data using Redaction type:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

"""
This example demonstrates how to retrieve data from the Skyflow vault using a list of Skyflow IDs.

1. Initializes the Skyflow client with a given vault ID.
2. Creates a request to retrieve records based on Skyflow IDs.
3. Specifies that the response should not return tokens.
4. Uses plain text redaction type for the retrieved records.
5. Prints the response to display the retrieved records.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of Skyflow IDs to retrieve records (replace with actual Skyflow IDs)
    ids = ['a581d205-1969-4350-acbe-a2a13eb871a6', '5ff887c3-b334-4294-9acc-70e78ae5164a']  # Replace with actual Skyflow IDs

    # Step 2: Create a GetRequest to retrieve records by Skyflow ID without returning tokens
    #  The request specifies:
    # - `ids`: The list of Skyflow IDs to retrieve
    # - `table`: The table from which the records will be retrieved
    # - `return_tokens`: Set to false, meaning tokens will not be returned in the response
    # - `redaction_type`: Set to PLAIN_TEXT, meaning the retrieved records will have data redacted as plain text
    get_by_id_request = GetRequest(
        table='table1',  # Replace with the actual table name
        ids=ids,
        return_tokens=False,   # Set to false to avoid returning tokens
        redaction_type=RedactionType.PLAIN_TEXT # Redact data as plain text
    )

    # Step 3: Send the request to the Skyflow vault and retrieve the records
    get_by_id_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').get(get_by_id_request)
    # Replace with actual Vault ID

    print(get_by_id_response) # Print the response to the console

# Step 5: Handle any errors that occur during the retrieval process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '4555555555555553',
            'email': 'john.doe@gmail.com',
            'name': 'john doe',
            'skyflow_id': 'a581d205-1969-4350-acbe-a2a13eb871a6'
        },
        {
            'card_number': '4555555555555559',
            'email': 'jane.doe@gmail.com',
            'name': 'jane doe',
            'skyflow_id': '5ff887c3-b334-4294-9acc-70e78ae5164a'
        }
    ],
    errors=[]
)
```

#### Get tokens
Return tokens for records. Ideal for securely processing sensitive data while maintaining data privacy.

An example of get call to retrieve tokens using Skyflow IDs:


```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

"""
This example demonstrates how to retrieve data from the Skyflow vault and return tokens along with the records.

1. Initializes the Skyflow client with a given vault ID.
2. Creates a request to retrieve records based on Skyflow IDs and ensures tokens are returned.
3. Prints the response to display the retrieved records along with the tokens.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of Skyflow IDs (replace with actual Skyflow IDs)
    ids = ['a581d205-1969-4350-acbe-a2a13eb871a6', '5ff887c3-b334-4294-9acc-70e78ae5164a']  # Replace with actual Skyflow IDs

    # Step 2: Create a GetRequest to retrieve records based on Skyflow IDs
    #  The request specifies:
    # - `ids`: The list of Skyflow IDs to retrieve
    # - `table`: The table from which the records will be retrieved
    # - `return_tokens`: Set to false, meaning tokens will not be returned in the response
    get_tokens_request = GetRequest(
        table='table1',  # Replace with the actual table name
        ids=ids,
        return_tokens=True,   # Set to false to avoid returning tokens
    )

    # Step 3: Send the request to the Skyflow vault and retrieve the records
    get_tokens_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').get(get_tokens_request)
    # Replace with actual Vault ID

    print(get_tokens_response) # Print the response to the console

# Step 5: Handle any errors that occur during the retrieval process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '3998-2139-0328-0697',
            'email': 'c9a6c9555060@82c092e7.bd52',
            'name': '82c092e7-74c0-4e60-bd52-c9a6c9555060',
            'skyflow_id': 'a581d205-1969-4350-acbe-a2a13eb871a6'
        },
        {
            'card_number': '3562-0140-8820-7499',
            'email': '6174366e2bc6@59f82e89.93fc',
            'name': '59f82e89-138e-4f9b-93fc-6174366e2bc6',
            'skyflow_id': '5ff887c3-b334-4294-9acc-70e78ae5164a'
        }
    ],
    errors=[]
)
```

#### Get by column name and column values
Retrieve records by unique column values. Ideal for querying data without knowing Skyflow IDs, using alternate unique identifiers.

An example of get call to retrieve data using column name and column values:

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RedactionType
from skyflow.vault.data import GetRequest

"""
This example demonstrates how to retrieve data from the Skyflow vault based on column values.

1. Initializes the Skyflow client with a given vault ID.
2. Creates a request to retrieve records based on specific column values (e.g., email addresses).
3. Prints the response to display the retrieved records after redacting sensitive data based on the specified redaction type.
"""
try:
    # Initialize Skyflow client
    # Step 1: Initialize a list of column values (email addresses in this case)
    column_values = [
        'john.doe@gmail.com',  # Example email address
        'jane.doe@gmail.com'   # Example email address
    ]

    # Step 2: Step 2: Create a GetRequest to retrieve records based on column values
    #  The request specifies:
    # - `ids`: The list of Skyflow IDs to retrieve
    # - `table`: The table from which the records will be retrieved
    # - `return_tokens`: Set to false, meaning tokens will not be returned in the response
    get_by_column_request = GetRequest(
        table='table1',   # Replace with the actual table name
        column_name='email',   # The column name to filter by (e.g., "email")
        column_values=column_values,  # The list of column values to match
        redaction_type=RedactionType.PLAIN_TEXT  # Set the redaction type (e.g., PLAIN_TEXT)
    )

    # Step 3: Send the request to the Skyflow vault and retrieve the records
    get_by_column_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').get(get_by_column_request)
    # Replace with actual Vault ID

    print(get_by_column_response) # Print the response to the console

# Step 5: Handle any errors that occur during the retrieval process
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes

```

Sample response:

```python
GetResponse(
    data=[
        {
            'card_number': '4555555555555553',
            'email': 'john.doe@gmail.com',
            'name': 'john doe',
            'skyflow_id': 'a581d205-1969-4350-acbe-a2a13eb871a6'
        },
        {
            'card_number': '4555555555555559',
            'email': 'jane.doe@gmail.com',
            'name': 'jane doe',
            'skyflow_id': '5ff887c3-b334-4294-9acc-70e78ae5164a'
        }
    ],
    errors=[]
)
```

#### Redaction Types

Redaction types determine how sensitive data is displayed when retrieved from the vault.
**Available Redaction Types**

- `DEFAULT`: Applies the vault-configured default redaction setting.
- `DEFAULT`: Completely removes sensitive data from view.
- `MASKED`: Partially obscures sensitive information.
- `PLAIN_TEXT`: Displays the full, unmasked data.

**Choosing the Right Redaction Type**
- Use `REDACTED` for scenarios requiring maximum data protection to prevent exposure of sensitive information.
- Use `MASKED` to provide partial visibility of sensitive data for less critical use cases.
- Use `PLAIN_TEXT` for internal, authorized access where full data visibility is necessary.

### Update

To update data in your vault, use the `update` method. The `UpdateRequest` class is used to create an update request, where you specify parameters such as the table name, data (as a dictionary), tokens, return_tokens, and token_strict. If `return_tokens` is set to True, Skyflow returns tokens for the updated records. If `return_tokens` is set to False, Skyflow returns IDs for the updated records.

#### Construct an update request

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import TokenMode
from skyflow.vault.data import UpdateRequest

"""
This example demonstrates how to update records in the Skyflow vault by providing new data and/or tokenized values, along with the corresponding UpdateRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Prepare the data to update in the vault
    # Use a dictionary to store the data that will be updated in the specified table
    update_data = {
        'skyflow_id': '<SKYFLOW_ID>',  # Skyflow ID for identifying the record to update
        '<COLUMN_NAME_1>': '<COLUMN_VALUE_1>',  # Example of a column name and its value to update
        '<COLUMN_NAME_2>': '<COLUMN_VALUE_2>'  # Another example of a column name and its value to update
    }

    # Step 2: Prepare the tokens (if necessary) for certain columns that require tokenization
    # Use a dictionary to specify columns that need tokens in the update request
    tokens = {
        '<COLUMN_NAME_2>': '<TOKEN_VALUE_2>'  # Example of a column name that should be tokenized
    }

    # Step 3: Create an UpdateRequest to specify the update operation
    # The request includes the table name, data, tokens, and the returnTokens flag
    update_request = UpdateRequest(
        table='<TABLE_NAME>',  # Replace with the actual table name to update
        token_mode=TokenMode.ENABLE,  # Specifies the tokenization mode (ENABLE means tokenization is applied)
        data=update_data,  # The data to update in the record
        tokens=tokens,  # The tokens associated with specific columns
        return_tokens=True  # Specify whether to return tokens in the response
    )

    # Step 4: Send the request to the Skyflow vault and update the record
    update_response = skyflow_client.vault('<VAULT_ID>').update(update_request)  # Replace with actual Vault ID

    # Step 5: Print the response to confirm the update result
    print(update_response)

except SkyflowError as error:
    # Step 6: Handle any errors that occur during the update operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

An example of update call

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import TokenMode
from skyflow.vault.data import UpdateRequest

"""
This example demonstrates how to update a record in the Skyflow vault with specified data and tokens.

1. Initializes the Skyflow client with a given vault ID.
2. Constructs an update request with data to modify and tokens to include.
3. Sends the request to update the record in the vault.
4. Prints the response to confirm the success or failure of the update operation.
"""

try:
    # Initialize Skyflow client
    # Step 1: Prepare the data to update in the vault
    # Use a dictionary to store the data that will be updated in the specified table
    update_data = {
        'skyflow_id': '5b699e2c-4301-4f9f-bcff-0a8fd3057413',  # Skyflow ID for identifying the record to update
        'name': 'john doe',  # Example of a column name and its value to update
        'card_number': '4111111111111115'  # Another example of a column name and its value to update
    }

    # Step 2: Prepare the tokens (if necessary) for certain columns that require tokenization
    # Use a dictionary to specify columns that need tokens in the update request
    tokens = {
        'name': '72b8ffe3-c8d3-4b4f-8052-38b2a7405b5a'  # Example of a column name that should be tokenized
    }

    # Step 3: Create an UpdateRequest to specify the update operation
    # The request includes the table name, data, tokens, and the returnTokens flag
    update_request = UpdateRequest(
        table='table1',  # Replace with the actual table name to update
        token_mode=TokenMode.ENABLE,  # Token mode enabled to allow tokenization of sensitive data
        data=update_data,  # The data to update in the record
        tokens=tokens,  # The tokenized values for sensitive columns
    )

    # Step 4: Send the request to the Skyflow vault and update the record
    update_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').update(update_request)  # Replace with actual Vault ID

    # Step 5: Print the response to confirm the update result
    print(update_response)

except SkyflowError as error:
    # Step 6: Handle any errors that occur during the update operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample response

- When `return_tokens` is set to `True`

```python
UpdateResponse(
    updated_field={
        'skyflow_id': '5b699e2c-4301-4f9f-bcff-0a8fd3057413',
        'name': '72b8ffe3-c8d3-4b4f-8052-38b2a7405b5a',
        'card_number': '4131-1751-0217-8491'
    },
    errors=[]
)

```

- When `return_tokens` is set to `False`

```python
UpdateResponse(
    updated_field={'skyflow_id': '5b699e2c-4301-4f9f-bcff-0a8fd3057413'},
    errors=[]
)

```

### Delete

To delete records using Skyflow IDs, use the `delete` method. The `DeleteRequest` class accepts a list of Skyflow IDs that you want to delete, as shown below:

#### Construct a delete request

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import DeleteRequest

"""
This example demonstrates how to delete records from a Skyflow vault using specified Skyflow IDs, along with corresponding DeleteRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Prepare a list of Skyflow IDs for the records to delete
    # The list stores the Skyflow IDs of the records that need to be deleted from the vault
    delete_ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>', '<SKYFLOW_ID3>']  # Replace with actual Skyflow IDs

    # Step 2: Create a DeleteRequest to define the delete operation
    # The request specifies the table from which to delete the records and the IDs of the records to delete
    delete_request = DeleteRequest(
        table='<TABLE_NAME>',  # Replace with the actual table name from which to delete
        ids=delete_ids  # List of Skyflow IDs to delete
    )

    # Step 3: Send the delete request to the Skyflow vault
    delete_response = skyflow_client.vault('<VAULT_ID>').delete(delete_request)  # Replace with your actual Vault ID
    print(delete_response)  # Print the response to confirm the delete result

except SkyflowError as error:
    # Step 4: Handle any exceptions that occur during the delete operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the exception stack trace for debugging purposes



```

An example of delete call

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import DeleteRequest

"""
This example demonstrates how to delete records from a Skyflow vault using specified Skyflow IDs.

1. Initializes the Skyflow client with a given Vault ID.
2. Constructs a delete request by specifying the IDs of the records to delete.
3. Sends the delete request to the Skyflow vault to delete the specified records.
4. Prints the response to confirm the success or failure of the delete operation.
"""

try:
    # Initialize Skyflow client
    # Step 1: Prepare a list of Skyflow IDs for the records to delete
    # The list stores the Skyflow IDs of the records that need to be deleted from the vault
    delete_ids = ['9cbf66df-6357-48f3-b77b-0f1acbb69280', 'ea74bef4-f27e-46fe-b6a0-a28e91b4477b', '47700796-6d3b-4b54-9153-3973e281cafb']  # Replace with actual Skyflow IDs

    # Step 2: Create a DeleteRequest to define the delete operation
    # The request specifies the table from which to delete the records and the IDs of the records to delete
    delete_request = DeleteRequest(
        table='table1',  # Replace with the actual table name from which to delete
        ids=delete_ids  # List of Skyflow IDs to delete
    )

    # Step 3: Send the delete request to the Skyflow vault
    delete_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').delete(delete_request)  # Replace with your actual Vault ID
    print(delete_response)  # Print the response to confirm the delete result
# Step 4: Handle any exceptions that occur during the delete operation
except SkyflowError as error:
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the exception stack trace for debugging purposes
```

Sample response:

```python
DeleteResponse(
    deleted_ids=[
        '9cbf66df-6357-48f3-b77b-0f1acbb69280',
        'ea74bef4-f27e-46fe-b6a0-a28e91b4477b',
        '47700796-6d3b-4b54-9153-3973e281cafb'
    ],
    errors=[]
)

```

### Query

To retrieve data with SQL queries, use the `query` method. `QueryRequest` is class that takes the `query` parameter as follows:

#### Construct a query request
Refer to [Query your data](https://docs.skyflow.com/query-data/) and [Execute Query](https://docs.skyflow.com/record/#QueryService_ExecuteQuery) for guidelines and restrictions on supported SQL statements, operators, and keywords.

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import QueryRequest

"""
This example demonstrates how to execute a custom SQL query on a Skyflow vault, along with QueryRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Define the SQL query to execute on the Skyflow vault
    # Replace "<YOUR_SQL_QUERY>" with the actual SQL query you want to run
    query = '<YOUR_SQL_QUERY>'  # Example: "SELECT * FROM table1 WHERE column1 = 'value'"

    # Step 2: Create a QueryRequest with the specified SQL query
    query_request = QueryRequest(
        query=query  # SQL query to execute
    )

    # Step 3: Execute the query request on the specified Skyflow vault
    query_response = skyflow_client.vault('<VAULT_ID>').query(query_request)  # Replace <VAULT_ID> with your actual Vault ID

    # Step 4: Print the response containing the query results
    print('Query Result:', query_response)

except SkyflowError as error:
    # Step 5: Handle any exceptions that occur during the query execution
    print('Skyflow Specific Error:', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    # Handle any unexpected errors during execution
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```
An example of query call

```python
from skyflow.error import SkyflowError
from skyflow.vault.data import QueryRequest

"""
This example demonstrates how to execute a SQL query on a Skyflow vault to retrieve data.

1. Initializes the Skyflow client with the Vault ID.
2. Constructs a query request with a specified SQL query.
3. Executes the query against the Skyflow vault.
4. Prints the response from the query execution.
"""

try:
    # Initialize Skyflow client
    # Step 1: Define the SQL query
    # Example query: Retrieve all records from the "cards" table with a specific skyflow_id
    query = "SELECT * FROM cards WHERE skyflow_id='3ea3861-x107-40w8-la98-106sp08ea83f'"  # Example: "SELECT * FROM table1 WHERE column1 = 'value'"

    # Step 2: Create a QueryRequest with the SQL query
    query_request = QueryRequest(
        query=query  # SQL query to execute
    )

    # Step 3: Execute the query request on the specified Skyflow vault
    query_response = skyflow_client.vault('9f27764a10f7946fe56b3258e117').query(query_request)  #  Vault ID: 9f27764a10f7946fe56b3258e117

    # Step 4: Print the response containing the query results
    print(query_response)

except SkyflowError as error:
    # Step 5: Handle any exceptions that occur during the query execution
    print('Skyflow Specific Error:', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })

except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample Response

```python
QueryResponse(
    fields=[
        {
            'card_number': 'XXXXXXXXXXXX1112',
            'name': 'S***ar',
            'skyflow_id': '3ea3861-x107-40w8-la98-106sp08ea83f',
            'tokenized_data': {}
        }
    ],
    errors=[]
)
```

### Connections

Skyflow Connections is a gateway service that uses tokenization to securely send and receive data between your systems and first- or third-party services. The connections module invokes both inbound and/or outbound connections.
- **Inbound connections**: Act as intermediaries between your client and server, tokenizing sensitive data before it reaches your backend, ensuring downstream services handle only tokenized data.
- **Outbound connections**: Enable secure extraction of data from the vault and transfer it to third-party services via your backend server, such as processing checkout or card issuance flows.

#### Invoke a connection
To invoke a connection, use the `invoke` method of the Skyflow client.
#### Construct an invoke connection request

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
