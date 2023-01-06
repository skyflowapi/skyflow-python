# Skyflow-python

---
## Description
This Python SDK is designed to help developers easily implement Skyflow into their python backend.



## Table of Contents
- [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
    - [Requirements](#requirements)
    - [Configuration](#configuration)
  - [Service Account Bearer Token Generation](#service-account-bearer-token-generation)
  - [Vault APIs](#vault-apis)
    - [Insert](#insert-data-into-the-vault)
    - [Detokenize](#detokenize)
    - [Get By Id](#get-by-id)
    - [Invoke Connection](#invoke-connection)
  - [Logging](#logging)
  - [Reporting a Vulnerability](#reporting-a-vulnerability)

## Features

Authentication with a Skyflow Service Account and generation of a bearer token

Vault API operations to insert, retrieve and tokenize sensitive data

Invoking connections to call downstream third party APIs without directly handling sensitive data

## Installation

### Requirements

- Python 3.7.0 and above

### Configuration

The package can be installed using pip:

```bash
pip install skyflow
```

## Service Account Bearer Token Generation

The [Service Account](https://github.com/skyflowapi/skyflow-python/tree/main/skyflow/service_account) python module is used to generate service account tokens from service account credentials file which is downloaded upon creation of service account. The token generated from this module is valid for 60 minutes and can be used to make API calls to vault services as well as management API(s) based on the permissions of the service account.

The `generate_bearer_token(filepath)` function takes the credentials file path for token generation, alternatively, you can also send the entire credentials as string, by using `generate_bearer_token_from_creds(credentials)`

[Example using filepath](https://github.com/skyflowapi/skyflow-python/blob/main/samples/sa_token_sample.py):

```python
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token, is_expired

# cache token for reuse
bearerToken = ''
tokenType = ''
def token_provider():
    global bearerToken
    global tokenType
    
    if is_expired(bearerToken):
        bearerToken, tokenType = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken, tokenType

try:
    accessToken, tokenType = token_provider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)

```


[Example using credentials string](https://github.com/skyflowapi/skyflow-python/blob/main/samples/generate_bearer_token_from_creds_sample.py):

```python
from skyflow.errors import SkyflowError
from skyflow.service_account import generate_bearer_token_from_creds, is_expired

# cache token for reuse
bearerToken = ''
tokenType = ''
def token_provider():
    global bearerToken
    global tokenType
    # As an example
    credentials = {
        "clientID": "<YOUR_clientID>",
        "clientName": "<YOUR_clientName>",
        "keyID": "<YOUR_keyID>",
        "tokenURI": '<YOUR_tokenURI>',
        "privateKey": "<YOUR_PEM_privateKey>"
    }
    jsonString = json.dumps(credentials)
    if is_expired(bearerToken):
        bearerToken, tokenType = generate_bearer_token_from_creds(
            credentials=jsonString)
    return bearerToken, tokenType

try:
    accessToken, tokenType = token_provider()
    print("Access Token:", accessToken)
    print("Type of token:", tokenType)
except SkyflowError as e:
    print(e)

```

## Vault APIs

The [Vault](https://github.com/skyflowapi/skyflow-python/tree/main/skyflow/vault) python module is used to perform operations on the vault such as inserting records, detokenizing tokens, retrieving tokens for a skyflow_id and to invoke a connection.

To use this module, the skyflow client must first be initialized as follows.

```python
from skyflow.vault import Client, Configuration
from skyflow.service_account import generate_bearer_token, is_expired

# cache for reuse
bearerToken = ''

# User defined function to provide access token to the vault apis
def token_provider():
    global bearerToken
    if is_expired(bearerToken):
        return bearerToken
    bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken

#Initializing a Skyflow Client instance with a SkyflowConfiguration object
config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', token_provider)
client = Client(config)
```

All Vault APIs must be invoked using a client instance.

### Insert data into the vault

To insert data into your vault use the `insert(records: dict, options: InsertOptions)` method. The `records` parameter is a dictionary that requires a `records` key and takes an array of records to insert into the vault. The `options` parameter takes a dictionary of optional parameters for the insertion. This includes an option to return tokenized data and upsert records.

```python
# Optional, indicates whether you return tokens for inserted data. Defaults to 'true'.
tokens: bool
# Optional, indicates Upsert support in the vault. 
upsert: [UpsertOption]  
```

Insert call schema
```python
from skyflow.vault import InsertOptions, UpsertOption
from skyflow.errors import SkyflowError

#Initialize Client
try:
    # Create an Upsert option.
    upsertOption =  UpsertOption(table="<TABLE_NAME>",column="<UNIQUE_COLUMN>") 
    options = InsertOptions(tokens=True,upsert=[upsertOption]) 

    data = {
        "records": [
            {
                "table": "<TABLE_NAME>",
                "fields": {
                    "<FIELDNAME>": "<VALUE>"
                }
            }
        ]
    }
    response = client.insert(data, options=options)
    print("Response:", response)
except SkyflowError as e:
    print("Error Occurred:", e)
```

**Insert call [example](https://github.com/skyflowapi/skyflow-python/blob/main/samples/insert_sample.py)**

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

Skyflow returns tokens for the record you just inserted.

```python
{
    "records": [
        {
            "table": "cards",
            "fields": {
                "cardNumber": "f3907186-e7e2-466f-91e5-48e12c2bcbc1",
                "cvv": "1989cb56-63da-4482-a2df-1f74cd0dd1a5",
            },
        }
    ]
}
```

**Insert call [example](https://github.com/skyflowapi/skyflow-python/blob/main/samples/insert_upsert_sample.py) with `upsert` options**

```python
upsertOption = UpsertOption(table="cards",column="cardNumber")
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
    InsertOptions(tokens=True,upsert=[upsertOption]),
)
```

Skyflow returns tokens, with `upsert` support, for the record you just inserted.

```python
{
    "records": [
        {
            "table": "cards",
            "fields": {
                "cardNumber": "f3907186-e7e2-466f-91e5-48e12c2bcbc1",
                "cvv": "1989cb56-63da-4482-a2df-1f74cd0dd1a5",
            },
        }
    ]
}
```

### Detokenize

In order to retrieve data from your vault using tokens that you have previously generated for that data, you can use the detokenize(records: dict) method. The records parameter takes a dictionary that contains the `records` key that takes an array of records to be fetched from the vault as shown below.

```python
{
  "records":[
    {
      "token": str     #token for the record to be fetched
    }
  ]
}
```

An [example](https://github.com/skyflowapi/skyflow-python/blob/main/samples/detokenize_sample.py) of a detokenize call:

```python
try:
    client.detokenize(
        {
            "records": [
                {"token": "45012507-f72b-4f5c-9bf9-86b133bae719"},
                {'token': 'invalid-token'}
            ]
        }
    )
except SkyflowError as e:
    if e.data:
        print(e.data) # see note below
    else:
        print(e)
```

Sample response:

```python
{
    "records": [
    {
      "token": "131e70dc-6f76-4319-bdd3-96281e051051",
      "value": "1990-01-01"
    }
  ],
  "errors": [
    {
       "token": "invalid-token",
       "error": {
         "code": 404,
         "description": "Tokens not found for invalid-token"
       }
   }
  ]
}
```

### Get By Id

For retrieving using SkyflowID's or Unique Column Values, use the get_by_id(records: dict) method. The records parameter takes a Dictionary that contains records to be fetched as shown below:

```python
{
    "records": [
        {
            "ids": [str],  # List of SkyflowID's of the records to be fetched
            "table": str,  # name of table holding the above skyflow_id's
            "redaction": Skyflow.RedactionType,  # redaction to be applied to retrieved data
        }
            (or)
             #To get records using unique column name and values.
        {
            "redaction" : "<REDACTION_TYPE>",
            "table": "<TABLE_NAME>",
            "columnName": "<UNIQUE_COLUMN_NAME>",
            "columnValues": "[<COLUMN_VALUE_1>,<COLUMN_VALUE_2>]",
        }
    ]
}
```

There are 4 accepted values in Skyflow.RedactionTypes:

- `PLAIN_TEXT`
- `MASKED`
- `REDACTED`
- `DEFAULT`

An [example](https://github.com/skyflowapi/skyflow-python/blob/main/samples/get_by_ids_sample.py) of get_by_id call:

```python
from skyflow.vault import RedactionType

skyflowIDs = [
    "f8d8a622-b557-4c6b-a12c-c5ebe0b0bfd9",
    "da26de53-95d5-4bdb-99db-8d8c66a35ff9"
]
record = {"ids": skyflowIDs, "table": "cards", "redaction": RedactionType.PLAIN_TEXT}
recordWithUniqueColumn = {"table": "cards", "redaction": ReadctionType.PLAIN_TEXT, "columnName":             "card_number", "columnValues": ["1234566789"]}

invalidID = ["invalid skyflow ID"]
badRecord = {"ids": invalidID, "table": "cards", "redaction": RedactionType.PLAIN_TEXT}

records = {"records": [record, badRecord, recordWithUniqueColumn]}

try:
    client.get_by_id(records)
except SkyflowError as e:
    if e.data:
        print(e.data) # see note below
    else:
        print(e)
```

Sample response:

```python
{
  "records": [
      {
          "fields": {
              "card_number": "4111111111111111",
              "cvv": "127",
              "expiry_date": "11/35",
              "fullname": "myname",
              "skyflow_id": "f8d8a622-b557-4c6b-a12c-c5ebe0b0bfd9"
          },
          "table": "cards"
      },
      {
          "fields": {
              "card_number": "4111111111111111",
              "cvv": "317",
              "expiry_date": "10/23",
              "fullname": "sam",
              "skyflow_id": "da26de53-95d5-4bdb-99db-8d8c66a35ff9"
          },
          "table": "cards"
      },
       {
          "fields": {
              "card_number": "1234566789",
              "cvv": "318",
              "expiry_date": "08/36",
              "fullname": "samuel",
              "skyflow_id": "56513264-fc45-41fa-9cb0-d1ad3602bc49"
          },
          "table": "cards"
      }
  ],
  "errors": [
      {
          "error": {
              "code": "404",
              "description": "No Records Found"
          },
          "skyflow_ids": ["invalid skyflow id"]
      }
  ]
}
```

`Note:` While using detokenize and get_by_id methods, there is a possibility that some or all of the tokens might be invalid. In such cases, the data from response consists of both errors and detokenized records. In the SDK, this will raise a SkyflowError Exception and you can retrieve the data from this Exception object as shown above.

### Invoke Connection

Using Skyflow Connection, end-user applications can integrate checkout/card issuance flow with their apps/systems. To invoke connection, use the invoke_connection(config: Skyflow.ConnectionConfig) method of the Skyflow client.

```python
config = ConnectionConfig(
  connectionURL: str, # connection url received when creating a skyflow connection integration
  methodName: Skyflow.RequestMethod,
  pathParams: dict,	# optional
  queryParams: dict,	# optional
  requestHeader: dict, # optional
  requestBody: dict,	# optional
)
client.invokeConnection(config)
```

`methodName` supports the following methods:

- GET
- POST
- PUT
- PATCH
- DELETE

**pathParams, queryParams, requestHeader, requestBody** are the JSON objects represented as dictionaries that will be sent through the connection integration url.

An [example](https://github.com/skyflowapi/skyflow-python/blob/main/samples/invoke_connection_sample.py) of invoke_connection:

```python
from skyflow.vault import ConnectionConfig, Configuration, RequestMethod

bearerToken = ''
def token_provider():
    global bearerToken
    if is_expired(bearerToken):
        return bearerToken
    bearerToken, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearerToken

try:
    config = Configuration('<YOUR_VAULT_ID>', '<YOUR_VAULT_URL>', token_provider)
    connectionConfig = ConnectionConfig('<YOUR_CONNECTION_URL>', RequestMethod.POST,
    requestHeader={
                'Content-Type': 'application/json',
                'Authorization': '<YOUR_CONNECTION_BASIC_AUTH>'
    },
    requestBody= # For third party integration
    {
        "expirationDate": {
            "mm": "12",
            "yy": "22"
        }
    },
    pathParams={'cardID': '<CARD_VALUE>'}) # param as in the example
    client = Client(config)

    response = client.invoke_connection(connectionConfig)
    print('Response:', response)
except SkyflowError as e:
    print('Error Occurred:', e)
```

Sample response:

```python
{
    "receivedTimestamp": "2021-11-05 13:43:12.534",
    "processingTimeinMs": 12,
    "resource": {
        "cvv2": "558"
    }
}
```

## Logging

The skyflow python SDK provides useful logging using python's inbuilt `logging` library. By default the logging level of the SDK is set to `LogLevel.ERROR`. This can be changed by using `set_log_level(logLevel)` as shown below:

```python
import logging
from skyflow import set_log_level, LogLevel

logging.basicConfig() # You can set the basic config here
set_log_level(LogLevel.INFO) # sets the skyflow SDK log level to INFO
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