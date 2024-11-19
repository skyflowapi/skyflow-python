from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import GetRequest

# To generate Bearer Token from credentials string.
skyflow_credentials_string = '{"clientID":"<YOUR_CLIENT_ID>","clientName":"<YOUR_CLIENT_NAME>","tokenURI":"<YOUR_TOKEN_URI>","keyID":"<YOUR_KEY_ID>","privateKey":"<YOUR_PRIVATE_KEY>"}'

# please pass one of api_key, token, credentials_string & path as credentials
credentials = {
        "token": "BEARER_TOKEN", # bearer token
        # api_key: "API_KEY", # API_KEY
        # path: "PATH", # path to credentials file
        # credentials_string: skyflow_credentials_string, # credentials as string
}

client = (
    Skyflow.builder()
    .add_vault_config({
           "vault_id": "VAULT_ID", # primary vault
           "cluster_id": "CLUSTER_ID", # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           "env": Env.PROD, # Env by default it is set to PROD
           "credentials": credentials # individual credentials
    })
    .add_skyflow_credentials(credentials) # skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.INFO) # set log level by default it is set to ERROR
    .build()
)

column_values = [
    'VALUE1',
    'VALUE2',
]

get_ids = ['SKYFLOW_ID1', 'SKYFLOW_ID2']


get_request = GetRequest(
    table = 'TABLE_NAME',
    column_name = "COLUMN_NAME",
    column_values = column_values
)

response = client.vault('VAULT_ID').get(get_request)

print(response)