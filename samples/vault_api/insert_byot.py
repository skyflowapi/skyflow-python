from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.error import SkyflowError
from skyflow.utils.enums import TokenStrict
from skyflow.vault.data import GetRequest, InsertRequest
from skyflow.vault.tokens import DetokenizeRequest

# To generate Bearer Token from credentials string.
skyflow_credentials_string = '{"clientID":"<YOUR_CLIENT_ID>","clientName":"<YOUR_CLIENT_NAME>","tokenURI":"<YOUR_TOKEN_URI>","keyID":"<YOUR_KEY_ID>","privateKey":"<YOUR_PRIVATE_KEY>"}'

# please pass one of api_key, token, credentials_string & path as credentials
credentials = {
        "token": "BEARER_TOKEN", # bearer token
        # api_key: "API_KEY", //API_KEY
        # path: "PATH", //path to credentials file
        # credentials_string: skyflow_credentials_string, // credentials as string
}

skyflow_client = (
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

#Initialize Client

try:
    insert_data = [
        {"<FIELD_NAME1>": '<VALUE1>'},
        {"<FIELD_NAME2>": '<VALUE2>'}
    ]

    token_data = [
        {"<FIELD_NAME1>": '<TOKEN1>'},
        {"<FIELD_NAME2>": '<TOKEN2>'}
    ]

    insert_request = InsertRequest(
        table_name='<TABLE_NAME>',
        values=insert_data,
        token_strict=TokenStrict.ENABLE,  # token strict is enabled,
        tokens=token_data,
    )

    response = skyflow_client.vault('VAULT_ID').insert(insert_request)
    print("Response:", response)
except SkyflowError as e:
    print("Error Occurred:", e)
