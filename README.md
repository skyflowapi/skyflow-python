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
- [Vault](#vault)
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
    - [Query](#query)
- [Detect](#detect)
    - [Deidentify Text](#deidentify-text)
    - [Reidentify Text](#reidentify-text)
    - [Deidentify File](#deidentify-file)
    - [Get Detect Run](#get-detect-run)
- [Connections](#connections)
    - [Invoke a connection](#invoke-a-connection)
- [Authenticate with bearer tokens](#authenticate-with-bearer-tokens)
    - [Generate a bearer token](#generate-a-bearer-token)
    - [Generate bearer tokens with context](#generate-bearer-tokens-with-context)
    - [Generate scoped bearer tokens](#generate-scoped-bearer-tokens)
    - [Generate signed data tokens](#generate-signed-data-tokens)
    - [Bearer token expiry edge case](#bearer-token-expiry-edge-case)
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
## Migration from V1 to V2

Below are the steps to migrate the Python SDK from V1 to V2.

### Authentication Options

In V2, we have introduced multiple authentication options. 
You can now provide credentials in the following ways: 

- **Passing credentials in ENV.** (`SKYFLOW_CREDENTIALS`) (**Recommended**)
- **API Key**
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
- For overriding behavior and priority order of credentials, please refer to [Initialize the client](#initialize-the-client) section in [Quickstart](#quickstart).

### Initializing the client

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

### Request & Response Structure

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
   table=table_name,
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

### Request Options

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
   table=table_name,        # Replace with the table name
   values=insert_data,
   return_tokens=False,          # Do not return tokens
   continue_on_error=False,      # Stop inserting if any record fails
   upsert='<UPSERT_COLUMN>',     # Replace with the column name used for upsert logic
   token_mode=TokenMode.DISABLE, # Disable BYOT
   tokens='<TOKENS>'             # Replace with tokens when TokenMode is ENABLE.
)
```

### Error Structure

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

```typescript
{
    "http_status": "<http_status>",
    "grpc_code": <grpc_code>,
    "http_code": <http_code>,
    "message": "<message>",
    "request_id": "<request_id>",
    "details": [ "<details>" ]
}
```

## Quickstart
Get started quickly with the essential steps: authenticate, initialize the client, and perform a basic vault operation. This section provides a minimal setup to help you integrate the SDK efficiently.

### Authenticate
You can use an API key to authenticate and authorize requests to an API. For authenticating via bearer tokens and different supported bearer token types, refer to the [Authenticate with bearer tokens](#authenticate-with-bearer-tokens) section. 

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
To insert data into your vault, use the `insert` method.  The `InsertRequest` class creates an insert request, which includes the values to be inserted as a list of records. Below is a simple example to get started. For advanced options, check out [Insert data into the vault](#insert-data-into-the-vault-1) section.

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
        table='table1',  # Specify the table in the vault where the data will be inserted
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

The [Vault](https://github.com/skyflowapi/skyflow-python/tree/v2/skyflow/vault) module performs operations on the vault, including inserting records, detokenizing tokens, and retrieving tokens associated with a skyflow_id.


### Insert data into the vault

Apart from using the `insert` method to insert data into your vault covered in [Quickstart](#quickstart), you can also specify options in `InsertRequest`, such as returning tokenized data, upserting records, or continuing the operation in case of errors.

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
        table='<TABLE_NAME>',  # Replace with the actual table name in your Skyflow vault
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
        table='table1',  # Specify the table in the vault where the data will be inserted
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
        table='table1',      # Specify the table in the vault where the data will be inserted
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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/detokenize_records.py) of a detokenize call

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

#### An example of a detokenize call with `continue_on_error` option:

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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/tokenize_records.py) of Tokenize call

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


#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/get_records.py) of a get call to retrieve data using Redaction type:

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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/get_records.py) of get call to retrieve tokens using Skyflow IDs:


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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/get_column_values.py) of get call to retrieve data using column name and column values:

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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/update_record.py) of update call

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

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/delete_records.py) of delete call

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
#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/query_records.py) of query call

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

## Detect
Skyflow Detect enables you to deidentify and reidentify sensitive data in text and files, supporting advanced privacy-preserving workflows. The Detect API supports the following operations:

### Deidentify Text
To deidentify text, use the `deidentify_text` method. The `DeidentifyTextRequest` class creates a deidentify text request, which includes the text to be deidentified and options for controlling the deidentification process.

#### Construct a Deidentify Text request

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import DetectEntities, TokenType
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat, Transformations
"""
This example demonstrates how to deidentify text, along with corresponding DeidentifyTextRequest schema. 
"""
try:
    # Initialize Skyflow client
    # Step 1: Create request with text to deidentify
    request = DeidentifyTextRequest(
        text="<TEXT_TO_DEIDENTIFY>",
        entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],  # Entities to detect
        token_format = TokenFormat(       # Specify the token format for deidentified entities
            default=TokenType.VAULT_TOKEN,
        ),
        transformations=Transformations(  # Specify custom transformations for entities
            shift_dates={
                "max_days": 30,
                "min_days": 10,
                "entities": [DetectEntities.DOB]
            }
        ),
        allow_regex_list=["<REGEX_PATTERN>"],  # Optional regex patterns to allow
        restrict_regex_list=["<REGEX_PATTERN>"]  # Optional regex patterns to restrict
    )

    # Step 2: Call deidentify_text
    deidentify_text_response = skyflow_client.detect('<VAULT_ID>').deidentify_text(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID
    
    # Step 3: Print the deidentified text response
    print('Response: ', deidentify_text_response)


except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

#### An example of Deidentify Text call

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import DetectEntities, TokenType
from skyflow.vault.detect import DeidentifyTextRequest, TokenFormat, Transformations
"""
 * Skyflow Text De-identification Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a deidentify text request with all available options
 * 4. Handle response and errors
"""
try:
    # Initialize Skyflow Client
    # Step 1: Create request with sample text containing sensitive data
    request = DeidentifyTextRequest(
        text="My SSN is 123-45-6789 and my card is 4111 1111 1111 1111.",
        entities=[
            DetectEntities.SSN,
            DetectEntities.CREDIT_CARD
        ],
        token_format = TokenFormat(       # Specify the token format for deidentified entities
            default=TokenType.VAULT_TOKEN,
        ),
        transformations=Transformations(  # Specify custom transformations for entities
            shift_dates={
                "max_days": 30,
                "min_days": 30,
                "entities": [DetectEntities.DOB]
            }
        )
    )

    # Step 2: Call deidentify_text
    deidentify_text_response = skyflow_client.detect('<VAULT_ID>').deidentify_text(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID
    
    # Step 3: Print the deidentified text response
    print('Response: ', deidentify_text_response)

except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample Response:
```python
DeidentifyTextResponse(
    processed_text='My SSN is [SSN_VqLazzA] and my card is [CREDIT_CARD_54lAgtk].',
    entities=[
        EntityInfo(
            token='SSN_VqLazzA',
            value='123-45-6789',
            text_index=TextIndex(start=10, end=21),
            processed_index=TextIndex(start=10, end=23),
            entity='SSN',
            scores={'SSN': 0.9383999705314636}
        ),
        EntityInfo(
            token='CREDIT_CARD_54lAgtk',
            value='4111 1111 1111 1111',
            text_index=TextIndex(start=37, end=56),
            processed_index=TextIndex(start=39, end=60),
            entity='CREDIT_CARD',
            scores={'CREDIT_CARD': 0.9050999879837036}
        )
    ],
    word_count=9,
    char_count=57
)
```

### Reidentify Text

To reidentify text, use the `reidentify_text` method. The `ReidentifyTextRequest` class creates a reidentify text request, which includes the redacted or deidentified text to be reidentified.

#### Construct a Reidentify Text request

```python
from skyflow.error import SkyflowError
from skyflow.vault.detect import ReidentifyTextRequest, ReidentifyFormat
"""
This example demonstrates how to reidentify text, along with corresponding ReidentifyTextRequest schema. 
"""
try:
    # Initialize Skyflow client
    # Step 1: Create request to reidentify
    request = ReidentifyTextRequest(
        text="<YOUR_REDACTED_TEXT>",  # Text containing tokens to reidentify
        redacted_entities=["<ENTITY_TYPE>"],  # Entities to show redacted
        masked_entities=["<ENTITY_TYPE>"],    # Entities to show masked
        plain_text_entities=["<ENTITY_TYPE>"]  # Entities to show as plain text
    )
    
    # Step 2: Call reidentify_text
    reidentify_text_response = skyflow_client.detect('<VAULT_ID>').reidentify_text(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID
    
    # Step 3: Print the reidentified text response
    print('Response: ', reidentify_text_response)

except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

#### An example for Reidentify Text call

```python
from skyflow.error import SkyflowError
from skyflow.vault.detect import ReidentifyTextRequest, ReidentifyFormat
from skyflow.utils.enums import DetectEntities
"""
 * Skyflow Text Re-identification Example
 * 
 * This example demonstrates how to:
 * 1. Configure credentials
 * 2. Set up vault configuration
 * 3. Create a reidentify text request
 * 4. Use all available options for reidentification
 * 5. Handle response and errors
"""
try:
    # Initialize Skyflow Client
    # Step 1: Create request with deidentified text
    request = ReidentifyTextRequest(
        text="My SSN is [SSN_VqLazzA] and my card is [CREDIT_CARD_54lAgtk].",
    )
    
    # Step 2: Call reidentify_text
    reidentify_text_response = skyflow_client.detect('<VAULT_ID>').reidentify_text(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID

    # Step 3: Print the reidentified text response
    print('Response: ', reidentify_text_response)

except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample Response:
```python
ReidentifyTextResponse(
    processed_text='My SSN is 123-45-6789 and my card is 4111 1111 1111 1111.'
)
```

### Deidentify File
To deidentify files, use the `deidentify_file` method. The `DeidentifyFileRequest` class creates a deidentify file request, supports providing either a file or a file path in class FileInput for de-identification, along with various configuration options.

#### Construct a Deidentify File request
```python
from skyflow.error import SkyflowError 
from skyflow.utils.enums import DetectEntities, MaskingMethod, DetectOutputTranscriptions
from skyflow.vault.detect import DeidentifyFileRequest, TokenFormat, Transformations, Bleep, FileInput
"""
This example demonstrates how to deidentify file, along with corresponding DeidentifyFileRequest schema. 
"""
try:
    # Initialize Skyflow client
    # Step 1: Open file for deidentification
    file_path="<FILE_PATH>"
    file = open(file_path, 'rb')  # Open the file in read-binary mode
    # Step 2: Create deidentify file request
    request = DeidentifyFileRequest(
        file=FileInput(file),  # File to de-identify (can also provide a file path)
        entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],  # Entities to detect
        
        # Token format configuration
        token_format=TokenFormat(
            default=True,
            vault_token=[DetectEntities.SSN]
        ),

        # Output configuration 
        output_directory='<OUTPUT_DIRECTORY_PATH>',  # Output directory for saving the deidentified file
        wait_time=15,  # Max wait time in seconds (max 64)

        # Image-specific options
        # output_processed_image=True,  # Include processed image
        # output_ocr_text=True,  # Include OCR text
        # masking_method=MaskingMethod.BLACKBOX,  # Masking method

        # PDF-specific options
        # pixel_density=1.5,  # PDF processing density
        # max_resolution=2000,  # Max PDF resolution

        # Audio-specific options
        # output_processed_audio=True,  # Include processed audio
        # output_transcription=DetectOutputTranscriptions.PLAINTEXT,  # Transcription type

        # Audio bleep configuration
        # bleep=Bleep(
        #     gain=5,  # Loudness in dB
        #     frequency=1000,  # Pitch in Hz
        #     start_padding=0.1,  # Start padding in seconds
        #     stop_padding=0.2  # End padding in seconds
        # )
    )

    # Step 3: Call deidentify_file
    deidentify_file_response = skyflow_client.detect('<VAULT_ID>').deidentify_file(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID
    
    # Step 3: Print the reidentified text response
    print('Response: ', deidentify_file_response)

except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

#### An example for Deidentify File call

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import DetectEntities, MaskingMethod, DetectOutputTranscriptions
from skyflow.vault.detect import DeidentifyFileRequest, TokenFormat, Bleep, FileInput
"""
 * Skyflow Deidentify File Example
 * 
 * This sample demonstrates how to use all available options for deidentifying files.
 * Supported file types: images (jpg, png, etc.), pdf, audio (mp3, wav), documents, 
 * spreadsheets, presentations, structured text.
"""
try:
    # Initialize Skyflow client
    # Step 1: Open file for deidentification
    file = open('sensitive_document.txt', 'rb') # Open the file in read-binary mode
    # Step 2: Create deidentify file request
    request = DeidentifyFileRequest(
        file=FileInput(file),  # File to de-identify (can also provide a file path)
        entities=[
            DetectEntities.SSN,
            DetectEntities.CREDIT_CARD
        ],
        # Token format configuration
        token_format=TokenFormat(
            default=True,
            vault_token=[DetectEntities.SSN]
        ),
        output_directory="/tmp/processed",  # Output directory for saving the deidentified file
        wait_time=30, # Max wait time in seconds (max 64)
    )
    
    # Step 3: Call deidentify_file
    deidentify_file_response = skyflow_client.detect('<VAULT_ID>').deidentify_file(request)
    # Replace <VAULT_ID> with your actual Skyflow vault ID
    
    # Step 3: Print the reidentified text response
    print('Response: ', deidentify_file_response)

except SkyflowError as error:
    # Step 4: Handle any exceptions that may occur during the insert operation
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
DeidentifyFileResponse(
    file='TXkgY2FyZCBudW1iZXIgaXMgW0NSRURJVF9DQVJEXQpteSBzZWNvbmQ…',  # Base64 encoded file content
    type='redacted_file',
    extension='txt',
    word_count=19,
    char_count=111,
    size_in_kb=0.11,
    duration_in_seconds=None,
    page_count=None,
    slide_count=None,
    entities=[
        {
            'file': 'W3sicHJvY2Vzc2VleHQiOiJDUkVESVRfQ0FSRCIsInRleHQiOiIxMjM0NTY0Nzg5MDEyMzQ1NiIsImxvY2F0aW9uIjp7InN0dF9pZHgiOjE4LCJlbmRfaWR4IjozNSwic3R0X2lkeF9wcm9jZXNzZWR…', # Base64 encoded JSON string of entities
            'type': 'entities',
            'extension': 'json'
        }
    ],
    run_id='83abcdef-2b61-4a83-a4e0-cbc71ffabffd',
    status='SUCCESS',
)
```

### Get Detect Run
To retrieve the results of a previously started file deidentification operation, use the `get_detect_run` method. The `GetDetectRunRequest` class is initialized with the run_id returned from a prior `deidentify_file` call.

#### Construct a Get Detect Run request

```python
from skyflow.error import SkyflowError
from skyflow.vault.detect import GetDetectRunRequest

"""
Example program to demonstrate get detect run using run id, along with corresponding GetDetectRunRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Create GetDetectRunRequest 
    request = GetDetectRunRequest(
        run_id='<RUN_ID_FROM_DEIDENTIFY_FILE>'  # Replace with runId from deidentify_file
    )

    # Step 2: Call get_detect_run
    get_detect_run_response = skyflow_client.detect('<VAULT_ID>').get_detect_run(request)
    # Replace <VAULT_ID> with your actual vault ID

    # Print the response from the get detect run operation
    print('Response: ', get_detect_run_response)

except SkyflowError as error:
    # Step 3: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes

```

#### An example for Get Detect Run Call

```python
from skyflow.error import SkyflowError
from skyflow.vault.detect import GetDetectRunRequest
"""
 * Skyflow Get Detect Run Example
 * 
 * This example demonstrates how to:
 * 1. Configure credentials
 * 2. Set up vault configuration
 * 3. Create a get detect run request
 * 4. Call getDetectRun to poll for file processing results
 * 5. Handle response and errors
"""
try:
    # Initialize Skyflow client
    # Step 1: Create GetDetectRunRequest
    request = GetDetectRunRequest(
        run_id="48ec05ba-96ec-4641-a8e2-35e066afef95"
    )
    
    # Step 2: Call get_detect_run
    get_detect_run_response = skyflow_client.detect('<VAULT_ID>').get_detect_run(request)
    # Replace <VAULT_ID> with your actual vault ID

    # Print the response from the get detect run operation
    print('Response: ', get_detect_run_response)

except SkyflowError as error:
    # Step 3: Handle any exceptions that may occur during the insert operation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    print('Unexpected Error:', error)  # Print the stack trace for debugging purposes
```

Sample Response:
```python
DeidentifyFileResponse(
    file='TXkgY2FyZCBudW1iZXIgaXMgW0NSRURJVF9DQVJEXQpteSBzZWNvbmQ…',  # Base64 encoded file content
    type='redacted_file',
    extension='txt',
    word_count=19,
    char_count=111,
    size_in_kb=0.11,
    duration_in_seconds=None,
    page_count=None,
    slide_count=None,
    entities=[
        {
            'file': 'W3sicHJvY2Vzc2VleHQiOiJDUkVESVRfQ0FSRCIsInRleHQiOiIxMjM0NTY0Nzg5MDEyMzQ1NiIsImxvY2F0aW9uIjp7InN0dF9pZHgiOjE4LCJlbmRfaWR4IjozNSwic3R0X2lkeF9wcm9jZXNzZWR…', # Base64 encoded JSON string of entities
            'type': 'entities',
            'extension': 'json'
        }
    ],
    run_id='48ec05ba-96ec-4641-a8e2-35e066afef95',
    status='SUCCESS',
)
```

Incase of invalid/expired RunId:

```python
DeidentifyFileResponse(
    file_base64=None,
    file=None,
    type='UNKNOWN',
    extension=None,
    word_count=None,
    char_count=None,
    size_in_kb=0.0,
    duration_in_seconds=None,
    page_count=None,
    slide_count=None,
    entities=[],
    run_id='1e9f321f-dd51-4ab1-a014-21212fsdfsd',
    status='UNKNOWN'
)
```

### Connections

Skyflow Connections is a gateway service that uses tokenization to securely send and receive data between your systems and first- or third-party services. The [connections](https://github.com/skyflowapi/skyflow-python/tree/v2/skyflow/vault/connection) module invokes both inbound and/or outbound connections.
- **Inbound connections**: Act as intermediaries between your client and server, tokenizing sensitive data before it reaches your backend, ensuring downstream services handle only tokenized data.
- **Outbound connections**: Enable secure extraction of data from the vault and transfer it to third-party services via your backend server, such as processing checkout or card issuance flows.

#### Invoke a connection
To invoke a connection, use the `invoke` method of the Skyflow client.
#### Construct an invoke connection request

```python
from skyflow.error import SkyflowError
from skyflow.utils.enums import RequestMethod
from skyflow.vault.connection import InvokeConnectionRequest

"""
This example demonstrates how to invoke an external connection using the Skyflow SDK, along with corresponding InvokeConnectionRequest schema.
"""

try:
    # Initialize Skyflow client
    # Step 1: Define the request body parameters
    # These are the values you want to send in the request body
    request_body = {
        '<COLUMN_NAME_1>': '<COLUMN_VALUE_1>', 
        '<COLUMN_NAME_2>': '<COLUMN_VALUE_2>'
    }

    # Step 2: Define the request headers
    # Add any required headers that need to be sent with the request
    request_headers = {
        '<HEADER_NAME_1>': '<HEADER_VALUE_1>',
        '<HEADER_NAME_2>': '<HEADER_VALUE_2>',
    }

    # Step 3: Define the path parameters
    # Path parameters are part of the URL and typically used in RESTful APIs
    path_params = {
        '<YOUR_PATH_PARAM_KEY_1>': '<YOUR_PATH_PARAM_VALUE_1>',
        '<YOUR_PATH_PARAM_KEY_2>': '<YOUR_PATH_PARAM_VALUE_2>'
    }

    # Step 4: Define the query parameters
    # Query parameters are included in the URL after a '?' and are used to filter or modify the response
    query_params = {
        '<YOUR_QUERY_PARAM_KEY_1>': '<YOUR_QUERY_PARAM_VALUE_1>',
        '<YOUR_QUERY_PARAM_KEY_2>': '<YOUR_QUERY_PARAM_VALUE_2>',
    }

    # Step 5: Build the InvokeConnectionRequest using the provided parameters
    invoke_connection_request = InvokeConnectionRequest(
        method=RequestMethod.POST,  # The HTTP method to use for the request (POST in this case)
        body=request_body,  # The body of the request
        headers=request_headers,  # The headers to include in the request
        path_params=path_params,  # The path parameters for the URL
        query_params=query_params  # The query parameters to append to the URL
    )

    # Step 6: Invoke the connection using the request
    # Replace '<CONNECTION_ID>' with the actual connection ID you are using
    response = skyflow_client.connection('<CONNECTION_ID>').invoke(invoke_connection_request)

    # Step 7: Print the response from the invoked connection
    # This response contains the result of the request sent to the external system
    print('Connection invocation successful: ', response)

except SkyflowError as error:
    # Step 8: Handle any exceptions that occur during the connection invocation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    # Print the exception stack trace for debugging
    print('Unexpected Error:', error)

```

`method` supports the following methods:

- GET
- POST
- PUT
- PATCH
- DELETE

**path_params, query_params, header, body** are the JSON objects represented as dictionaries that will be sent through the connection integration url.

#### An [example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/vault_api/invoke_connection.py) of Invoke Connection

```python
from skyflow import Skyflow, LogLevel
from skyflow.error import SkyflowError
from skyflow.utils.enums import RequestMethod
from skyflow.vault.connection import InvokeConnectionRequest

"""
This example demonstrates how to invoke an external connection using the Skyflow SDK.
It configures a connection, sets up the request, and sends a POST request to the external service.

1. Initialize Skyflow client with connection details.
2. Define the request body, headers, and method.
3. Execute the connection request.
4. Print the response from the invoked connection.
"""

try:
    # Initialize Skyflow client
    # Step 1: Set up credentials and connection configuration
    # Load credentials from a JSON file (you need to provide the correct path)
    credentials = {
        'path': '/path/to/credentials.json'
    }

    # Define the connection configuration (URL and credentials)
    connection_config = {
        'connection_id': '<CONNECTION_ID>',  # Replace with actual connection ID
        'connection_url': 'https://connection.url.com',  # Replace with actual connection URL
        'credentials': credentials  # Set credentials for the connection
    }

    # Initialize the Skyflow client with the connection configuration
    skyflow_client = (
        Skyflow.builder()
        .add_connection_config(connection_config) # Add connection configuration to client
        .set_log_level(LogLevel.DEBUG)  # Set log level to DEBUG for detailed logs
        .build()  # Build the Skyflow client instance
    )

    # Step 2: Define the request body and headers
    request_body = {
        'card_number': '4337-1696-5866-0865', # Example card number
        'ssn': '524-41-4248'  # Example SSN
    }

    # Add any required headers that need to be sent with the request
    request_headers = {
        'Content-Type': 'application/json',  # Set content type for the request
    }

    # Step 3: Build the InvokeConnectionRequest with required parameters
    # Set HTTP method to POST, include the request body and headers
    invoke_connection_request = InvokeConnectionRequest(
        method=RequestMethod.POST,  # The HTTP method to use for the request (POST in this case)
        body=request_body,  # The body of the request
        headers=request_headers,  # The headers to include in the request
    )

    # Step 4: Invoke the connection using the request
    # Replace '<CONNECTION_ID>' with the actual connection ID you are using
    response = skyflow_client.connection('<CONNECTION_ID>').invoke(invoke_connection_request)

    # Step 5: Print the response from the invoked connection
    # This response contains the result of the request sent to the external system
    print('Connection invocation successful: ', response)

except SkyflowError as error:
    # Step 6: Handle any exceptions that occur during the connection invocation
    print('Skyflow Specific Error: ', {
        'code': error.http_code,
        'message': error.message,
        'details': error.details
    })
except Exception as error:
    # Print the exception stack trace for debugging
    print('Unexpected Error:', error)
```

Sample response:

```python
ConnectionResponse(
    {
        'card_number': '4337-1696-5866-0865',
        'ssn': '524-41-4248',
        'request_id': '4a3453b5-7aa4-4373-98d7-cf102b1f6f97'
    }
)

```

### Authenticate with bearer tokens
This section covers methods for generating and managing tokens to authenticate API calls:

- **Generate a bearer token:**  
Enable the creation of bearer tokens using service account credentials. These tokens, valid for 60 minutes, provide secure access to Vault services and management APIs based on the service account's permissions. Use this for general API calls when you only need basic authentication without additional context or role-based restrictions.
- **Generate a bearer token with context:**  
Support embedding context values into bearer tokens, enabling dynamic access control and the ability to track end-user identity. These tokens include context claims and allow flexible authorization for Vault services. Use this when policies depend on specific contextual attributes or when tracking end-user identity is required.
- **Generate a scoped bearer token:**  
Facilitate the creation of bearer tokens with role-specific access, ensuring permissions are limited to the operations allowed by the designated role. This is particularly useful for service accounts with multiple roles. Use this to enforce fine-grained role-based access control, ensuring tokens only grant permissions for a specific role.
- **Generate signed data tokens:**  
Add an extra layer of security by digitally signing data tokens with the service account's private key. These signed tokens can be securely detokenized, provided the necessary bearer token and permissions are available. Use this to add cryptographic protection to sensitive data, enabling secure detokenization with verified integrity and authenticity.

#### Generate a bearer token
The [Service Account](https://github.com/skyflowapi/skyflow-python/tree/v2/skyflow/service_account) Python package generates service account tokens using a service account credentials file, which is provided when a service account is created. The tokens generated by this module are valid for 60 minutes and can be used to make API calls to the [Data](https://docs.skyflow.com/record/) and [Management](https://docs.skyflow.com/management/) APIs, depending on the permissions assigned to the service account.

The `generate_bearer_token(filepath)` function takes the credentials file path for token generation, alternatively, you can also send the entire credentials as string, by using `generate_bearer_token_from_creds(credentials)`

#### [Example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/service_account/token_generation_example.py):

```python
import json
from skyflow.error import SkyflowError
from skyflow.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

# Example program to generate a Bearer Token using Skyflow's service account utilities.
# The token can be generated in two ways:
# 1. Using the file path to a credentials.json file.
# 2. Using the JSON content of the credentials file as a string.

# Variable to store the generated token
bearer_token = ''

# Example 1: Generate Bearer Token using a credentials.json file
try:
    # Specify the full file path to the credentials.json file
    file_path = 'CREDENTIALS_FILE_PATH'

    # Check if the token is already generated and still valid
    if not is_expired(bearer_token):
        print("Generated Bearer Token (from file):", bearer_token)
    else:
        # Generate a new Bearer Token from the credentials file
        token, _ = generate_bearer_token(file_path) # Set credentials from the file path
        bearer_token = token
        # Print the generated Bearer Token to the console
        print("Generated Bearer Token (from file):", bearer_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating token from file path: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating token from file path: {e}")

# Example 2: Generate Bearer Token using the credentials JSON string
try:
    # Provide the credentials JSON content as a string
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }

    # Convert credentials dictionary to JSON string
    credentials_string = json.dumps(skyflow_credentials)

    # Check if the token is either not initialized or has expired
    if not is_expired(bearer_token):
        print("Generated Bearer Token (from string):", bearer_token)
    else:
        # Generate a new Bearer Token from the credentials string
        token, _ = generate_bearer_token_from_creds(credentials_string)
        bearer_token = token
        print("Generated Bearer Token (from string):", bearer_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating token from credentials string: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating token from credentials string: {e}")
```

#### Generate bearer tokens with context
**Context-aware authorization** embeds context values into a bearer token during its generation and so you can reference those values in your policies. This enables more flexible access controls, such as helping you track end-user identity when making API calls using service accounts, and facilitates using signed data tokens during detokenization.

A service account with the context_id identifier generates bearer tokens containing context information, represented as a JWT claim in a Skyflow-generated bearer token. Tokens generated from such service accounts include a context_identifier claim, are valid for 60 minutes, and can be used to make API calls to the Data and Management APIs, depending on the service account's permissions.

#### [Example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/service_account/token_generation_with_context_example.py):
```python
import json
from skyflow.error import SkyflowError
from skyflow.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

"""
Example program to generate a Bearer Token using Skyflow's BearerToken utility.
The token is generated using two approaches:
1. By providing the credentials.json file path.
2. By providing the contents of credentials.json as a string.
"""

# Variable to store the generated token
bearer_token = ''

# Approach 1: Generate Bearer Token by specifying the path to the credentials.json file
try:
    # Replace <YOUR_CREDENTIALS_FILE_PATH> with the full path to your credentials.json file
    file_path = 'YOUR_CREDENTIALS_FILE_PATH'

    # Set context string (example: "abc")
    options = {'ctx': 'abc'}

    # Check if the token is already generated and still valid
    if not is_expired(bearer_token):
        print("Generated Bearer Token (from file):", bearer_token)
    else:
        # Generate a new Bearer Token from the credentials file
        token, _ = generate_bearer_token(file_path, options) # Set credentials from the file path and options
        bearer_token = token
        # Print the generated Bearer Token to the console
        print("Generated Bearer Token (from file):", bearer_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating token from file path: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating token from file path: {e}")

# Approach 2: Generate Bearer Token by specifying the contents of credentials.json as a string
try:
    # Provide the credentials JSON content as a string
    skyflow_credentials = {
        'clientID': '<YOUR_CLIENT_ID>',
        'clientName': '<YOUR_CLIENT_NAME>',
        'tokenURI': '<YOUR_TOKEN_URI>',
        'keyID': '<YOUR_KEY_ID>',
        'privateKey': '<YOUR_PRIVATE_KEY>',
    }

    # Convert credentials dictionary to JSON string
    credentials_string = json.dumps(skyflow_credentials)

    # Set context string (example: "abc")
    options = {'ctx': 'abc'}

    # Check if the token is either not initialized or has expired
    if not is_expired(bearer_token):
        print("Generated Bearer Token (from string):", bearer_token)
    else:
        # Generate a new Bearer Token from the credentials string and options
        token, _ = generate_bearer_token_from_creds(credentials_string, options)
        bearer_token = token
        print("Generated Bearer Token (from string):", bearer_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating token from file path: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating token from credentials string: {e}")
```

#### Generate scoped bearer tokens
A service account with multiple roles can generate bearer tokens with access limited to a specific role by specifying the appropriate roleID. This can be used to limit access to specific roles for services with multiple responsibilities, such as segregating access for billing and analytics. The generated bearer tokens are valid for 60 minutes and can only execute operations permitted by the permissions associated with the designated role.

#### [Example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/service_account/scoped_token_generation_example.py):
```python
import json
from skyflow.error import SkyflowError
from skyflow.service_account import (
    generate_bearer_token,
    generate_bearer_token_from_creds,
    is_expired,
)

"""
Example program to generate a Scoped Token using Skyflow's BearerToken utility.
The token is generated by providing the file path to the credentials.json file 
and specifying roles associated with the token.
"""

# Variable to store the generated token
scoped_token = ''

# Example: Generate Scoped Token by specifying the credentials.json file path
try:
    # Specify the full file path to the service account's credentials.json file
    file_path = 'YOUR_CREDENTIALS_FILE_PATH'

    # Set context string (example: "abc")
    options = {'role_ids': ['ROLE_ID']}

    # Check if the token is already generated and still valid
    if not is_expired(scoped_token):
        print("Generated Bearer Token (from file):", scoped_token)
    else:
        # Generate a new Bearer Token from the credentials file and associated roles
        scoped_token, _ = generate_bearer_token(file_path, options) # Set credentials from the file path and options
        # Print the generated Bearer Token to the console
        print("Generated Bearer Token (from file):", scoped_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating token from file path: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating token from file path: {e}")
```

#### Generate signed data tokens
Skyflow generates data tokens when sensitive data is inserted into the vault. These data tokens can be digitally signed with a service account's private key, adding an extra layer of protection. Signed tokens can only be detokenized by providing the signed data token along with a bearer token generated from the service account's credentials. The service account must have the necessary permissions and context to successfully detokenize the signed data tokens.

#### [Example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/service_account/signed_token_generation_example.py):
```python
import json
from skyflow.error import SkyflowError
from skyflow.service_account import (
    generate_signed_data_tokens,
    generate_signed_data_tokens_from_creds,
)

# Example program to generate Signed Data Tokens using Skyflow's utilities.
# Signed Data Tokens can be generated in two ways:
# 1. By specifying the file path to the credentials.json file.
# 2. By providing the credentials as a JSON string.

# Example 1: Generate Signed Data Tokens using a credentials file
try:
    # File path to the service account's credentials.json file
    file_path = "CREDENTIALS_FILE_PATH"

    # Options for generating signed data tokens
    options = {
        "ctx": "CONTEX_ID",  # Set the context value
        "data_tokens": ["DATA_TOKEN1", "DATA_TOKEN2"],  # Set the data tokens to be signed
        "time_to_live": 30,  # Set the data tokens to be signed
    }

    # Generate and retrieve the signed data tokens
    data_token, signed_data_token = generate_signed_data_tokens(file_path, options)
    # Print the signed data tokens to the console
    print("Signed Data Tokens (from file):", data_token, signed_data_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating signed token from file path: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating signed token from file path: {e}")

# Example 2: Generate Signed Data Tokens using credentials as a JSON string
try:
    # JSON object containing Skyflow credentials
    skyflow_credentials = {
        "clientID": "<YOUR_CLIENT_ID>",
        "clientName": "<YOUR_CLIENT_NAME>",
        "tokenURI": "<YOUR_TOKEN_URI>",
        "keyID": "<YOUR_KEY_ID>",
        "privateKey": "<YOUR_PRIVATE_KEY>",
    }

    # Convert credentials dictionary to JSON string
    credentials_string = json.dumps(skyflow_credentials)

    options = {
        "ctx": "CONTEX_ID",  # Context value associated with the token
        "data_tokens": ["DATA_TOKEN1", "DATA_TOKEN2"],  # Set the data tokens to be signed
        "time_to_live": 30,  # Set the token's time-to-live (TTL) in seconds
    }

    # Generate and retrieve the signed data tokens
    data_token, signed_data_token = generate_signed_data_tokens_from_creds(credentials_string, options)
    # Print the signed data tokens to the console
    print("Signed Data Tokens (from string):", data_token, signed_data_token)
except SkyflowError as error:
    # Handle any exceptions encountered during the token generation process
    print(f"Error generating signed token from credentials string: {error}")
except Exception as e:
    # Handle any other unexpected exceptions
    print(f"Error generating signed token from credentials string: {e}")

```

Notes:
- The `time_to_live` (TTL) value should be specified in seconds.
- By default, the TTL value is set to 60 seconds.

#### Bearer token expiry edge case
When you use bearer tokens for authentication and API requests in SDKs, there's the potential for a token to expire after the token is verified as valid but before the actual API call is made, causing the request to fail unexpectedly due to the token's expiration. An error from this edge case would look something like this:

```txt
message: Authentication failed. Bearer token is expired. Use a valid bearer token. See https://docs.skyflow.com/api-authentication/
```

If you encounter this kind of error, retry the request. During the retry, the SDK detects that the previous bearer token has expired and generates a new one for the current and subsequent requests.

#### [Example](https://github.com/skyflowapi/skyflow-python/blob/v2/samples/service_account/bearer_token_expiry_example.py):
```python
import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

"""
  * This example demonstrates how to configure and use the Skyflow SDK
  * to detokenize sensitive data stored in a Skyflow vault.
  * It includes setting up credentials, configuring the vault, and
  * making a detokenization request. The code also implements a retry
  * mechanism to handle unauthorized access errors (HTTP 401).
"""


def detokenize_data(skyflow_client, vault_id):
    try:
        # Creating a list of tokens to be detokenized
        detokenize_data = [
            {
                'token': '<TOKEN1>',
                'redaction': RedactionType.REDACTED
            },
            {
                'token': '<TOKEN2>',
                'redaction': RedactionType.MASKED
            }
        ]

        # Building a detokenization request
        detokenize_request = DetokenizeRequest(
            data=detokenize_data,
            continue_on_error=False
        )

        # Sending the detokenization request and receiving the response
        response = skyflow_client.vault(vault_id).detokenize(detokenize_request)

        # Printing the detokenized response
        print('Detokenization successful:', response)

    except SkyflowError as error:
        print("Skyflow error occurred:", error)
        raise

    except Exception as error:
        print("Unexpected error occurred:", error)
        raise


def perform_detokenization():
    try:
        # Setting up credentials for accessing the Skyflow vault
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',
            'clientName': '<YOUR_CLIENT_NAME>',
            'tokenURI': '<YOUR_TOKEN_URI>',
            'keyID': '<YOUR_KEY_ID>',
            'privateKey': '<YOUR_PRIVATE_KEY>',
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)  # Credentials string for authentication
        }

        credentials = {
            'token': '<YOUR_TOKEN>'
        }

        # Configuring the Skyflow vault with necessary details
        primary_vault_config = {
            'vault_id': '<YOUR_VAULT_ID1>',      # Vault ID
            'cluster_id': '<YOUR_CLUSTER_ID1>',  # Cluster ID
            'env': Env.PROD,                     # Environment set to PROD
            'credentials': credentials           # Setting credentials
        }

        # Creating a Skyflow client instance with the configured vault
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)
            .set_log_level(LogLevel.ERROR)      # Setting log level to ERROR
            .build()
        )

        # Attempting to detokenize data using the Skyflow client
        try:
            detokenize_data(skyflow_client, primary_vault_config.get('vault_id'))
        except SkyflowError as err:
            # Retry detokenization if the error is due to unauthorized access (HTTP 401)
            if err.http_code == 401:
                print("Unauthorized access detected. Retrying...")
                detokenize_data(skyflow_client, primary_vault_config.get('vault_id'))
            else:
                # Rethrow the exception for other error codes
                raise err

    except SkyflowError as error:
        print('Skyflow Specific Error:', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the function
perform_detokenization()
```

## Logging

The  SDK provides logging using python's inbuilt `logging` library. By default the logging level of the SDK is set to `LogLevel.ERROR`. This can be changed by using `set_log_level(log_level)` as shown below:

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

```python
import json
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env

"""
This example demonstrates how to configure the Skyflow client with custom log levels and authentication credentials (either token, credentials string, or other methods). It also shows how to configure a vault connection using specific parameters.
1. Set up credentials with a Bearer token or credentials string.
2. Define the Vault configuration.
3. Build the Skyflow client with the chosen configuration and set log level.
4. Example of changing the log level from ERROR (default) to INFO.
"""

# Step 1: Set up credentials - either pass token or use credentials string
# In this case, we are using a Bearer token for authentication
credentials = {
        'token': '<BEARER_TOKEN>', # Replace with actual Bearer token
}

# Step 2: Define the Vault configuration
# Configure the vault with necessary details like vault ID, cluster ID, and environment
vault_config = {
    'vault_id': '<VAULT_ID>', # Replace with actual Vault ID (primary vault)
    'cluster_id': '<CLUSTER_ID>', # Replace with actual Cluster ID (from vault URL)
    'env': Env.PROD, # Set the environment (default is PROD)
    'credentials': credentials # Set credentials for the vault (either token or credentials)
}

# Step 3: Define additional Skyflow credentials (optional, if needed for credentials string)
skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',     # Replace with your client ID
    'clientName': '<YOUR_CLIENT_NAME>', # Replace with your client name
    'tokenURI': '<YOUR_TOKEN_URI>',     # Replace with your token URI
    'keyID': '<YOUR_KEY_ID>',           # Replace with your key ID
    'privateKey': '<YOUR_PRIVATE_KEY>', # Replace with your private key
}

# Convert the credentials object to a json string format to be used for generating a Bearer Token
credentials_string = json.dumps(skyflow_credentials) # Set credentials string

# Step 4: Build the Skyflow client with the chosen configuration and log level
skyflow_client = (
    Skyflow.builder()
        .add_vault_config(vault_config)       # Add the Vault configuration
        .add_skyflow_credentials(skyflow_credentials) # Use Skyflow credentials if no token is passed
        .set_log_level(LogLevel.INFO) # Set log level to INFO (default is ERROR)
        .build() # Build the Skyflow client
)

# Now, the Skyflow client is ready to use with the specified log level and credentials
print('Skyflow client has been successfully configured with log level: INFO.')
```

## Reporting a Vulnerability

If you discover a potential security issue in this project, please reach out to us at **security@skyflow.com**. Please do not create public GitHub issues or Pull Requests, as malicious actors could potentially view them.
