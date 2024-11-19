from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import QueryRequest

# To generate Bearer Token from credentials string.
skyflow_credentials_string = '{"clientID":"<YOUR_CLIENT_ID>","clientName":"<YOUR_CLIENT_NAME>","tokenURI":"<YOUR_TOKEN_URI>","keyID":"<YOUR_KEY_ID>","privateKey":"<YOUR_PRIVATE_KEY>"}'

# please pass one of api_key, token, credentials_string & path as credentials
credentials = {
        "token": "BEARER_TOKEN", # bearer token
        # api_key: "API_KEY", # API_KEY
        # path: "PATH", # path to credentials file
        # credentials_string: skyflow_credentials_string, # credentials as string
}

skyflow_client = (
    Skyflow.builder()
    .add_vault_config({
           "vault_id": "VAULT_ID", # primary vault
           "cluster_id": "CLUSTER_ID", # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           "env": Env.PROD, # Env by default it is set to PROD
           "credentials": credentials # individual credentials
    })
    .add_connection_config({
        "connection_id": "CONNECTION_ID",
        "connection_url": "CONNECTION_URL",
        "credentials": credentials
    })
    .add_skyflow_credentials(credentials) # skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.INFO) # set log level by default it is set to ERROR
    .build()
)

# sample query
query = "select * from TABLE_NAME limit 1"


query_request = QueryRequest(
    query= query
)

response = skyflow_client.vault("VAULT_ID").query(query_request)

print(response)
