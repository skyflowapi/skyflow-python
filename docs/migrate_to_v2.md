# Migrate from v1 to v2

This guide outlines the steps required to migrate the Skyflow Python SDK from version 1 (v1) to version 2 (v2).

## Authentication

In v2, multiple authentication options have been introduced. You can now provide credentials in the following ways:

- **Passing credentials in ENV** (`SKYFLOW_CREDENTIALS`) (**Recommended**)
- **API Key**
- **Path to your credentials JSON file**
- **Stringified JSON of your credentials**
- **Bearer token**

These options allow you to choose the authentication method that best suits your use case.

### v1 (Old): Passing the token provider function below as a parameter to the Configuration.

```python
# User defined function to provide access token to the vault apis
def token_provider():
    global bearer_token
    if not is_expired(bearer_token):
        return bearer_token
    bearer_token, _ = generate_bearer_token('<YOUR_CREDENTIALS_FILE_PATH>')
    return bearer_token
```

#### v2 (New): Passing one of the following:

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
    'credentials_string': '<YOUR_CREDENTIALS_STRING>', # Credentials as string
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

### Initializing the client

In v2, we have introduced a Builder design pattern for client initialization and added support for multi-vault. This allows you to configure multiple vaults during client initialization. 

During client initialization, you can pass the following parameters:

- **`vault_id`** and **`cluster_id`**: These values are derived from the vault ID & vault URL.
- **`env`**: Specify the environment (e.g., SANDBOX or PROD).
- **`credentials`**: The necessary authentication credentials.

#### v1 (Old):

```python
# Initializing a Skyflow Client instance with a SkyflowConfiguration object
config = Configuration('<VAULT_ID>', '<VAULT_URL>', token_provider)
client = Client(config)
```

#### v2 (New):

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
- `vault_url` replaced with `cluster_id`.
- Added environment specification (`env`).
- Instance-specific log levels.

### Request & Response Structure

In v2, with the introduction of constructor parameters, you can now pass parameters to `InsertRequest`. This request needs 
- **`table_name`**: The name of the table.
- **`values`**: An array of objects containing the data to be inserted.
The response will be of type `InsertResponse` class, which contains `inserted_fields` and errors.

**Note:** Similar patterns apply to other operations like Get, Update, Delete. See the [README](../README.md) for complete examples.

#### v1 (Old): Request Building

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

#### v2 (New): Request Building

```python
from skyflow.vault.data import InsertRequest

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

#### v1 (Old): Response Structure

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

#### v2 (New): Response Structure

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

In v2, we have introduced constructor parameters, allowing you to set options as key-value pairs as parameters in request.

#### v1 (Old):

```python
options = InsertOptions(
    tokens = True
)
```

#### v2 (New):

```python
insert_request = InsertRequest(
    table=table_name,             # Replace with the table name
    values=insert_data,
    return_tokens=False,          # Do not return tokens
    continue_on_error=False,      # Stop inserting if any record fails
    upsert='<UPSERT_COLUMN>',     # Replace with the column name used for upsert logic, if any
    token_mode=TokenMode.DISABLE, # Disable BYOT
    tokens='<TOKENS>'             # Set with tokens when TokenMode is ENABLE
)
```

### Error Structure

In v2, we have enriched the error details to provide better debugging capabilities. 
The error response now includes: 
- **http_status**: The HTTP status code. 
- **grpc_code**: The gRPC code associated with the error. 
- **details** & **message**: A detailed description of the error. 
- **request_id**: A unique request identifier for easier debugging.

#### v1 (Old) Error Structure:

```json
{
  "code": "<http_code>",
  "message": "<message>"
}
```

#### v2 (New) Error Structure:

```python
{
    "http_status": "<http_status>",
    "grpc_code": <grpc_code>,
    "http_code": <http_code>,
    "message": "<message>",
    "request_id": "<request_id>",
    "details": [ "<details>" ]
}
```