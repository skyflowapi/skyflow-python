import json
from skyflow import Skyflow, LogLevel
from skyflow import Env
from skyflow.vault.data import DeleteRequest

skyflow_credentials = {
    'clientID': '<YOUR_CLIENT_ID>',
    'clientName': '<YOUR_CLIENT_NAME>',
    'tokenURI': '<YOUR_TOKEN_URI>',
    'keyID': '<YOUR_KEY_ID>',
    'privateKey': '<YOUR_PRIVATE_KEY>',
}
credentials_string = json.dumps(skyflow_credentials)

credentials = {
    'token': 'BEARER_TOKEN',  # bearer token
    # api_key: 'API_KEY', # API_KEY
    # path: 'PATH', # path to credentials file
    # credentials_string: credentials_string, # credentials as string
}

skyflow_client = (
    Skyflow.builder()
    .add_vault_config(
        {
            'vault_id': '<VAULT_ID1>',  # primary vault
            'cluster_id': '<CLUSTER_ID1>',  # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
            'env': Env.PROD,  # Env by default it is set to PROD
        }
    )
    .add_vault_config(
        {
            'vault_id': '<VAULT_ID2>',
            'cluster_id': '<CLUSTER_ID2>',  # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
            'env': Env.PROD,  # Env by default it is set to PROD
            'credentials': credentials,
        }
    )
    .add_skyflow_credentials(
        credentials
    )  # skyflow credentials will be used if no individual credentials are passed
    .set_log_level(LogLevel.ERROR)  # set log level by default it is set to ERROR
    .build()
)

primary_delete_ids = [
    'SKYFLOW_ID1',
    'SKYFLOW_ID2',
    'SKYFLOW_ID3',
]

# perform operations

primary_delete_request = DeleteRequest(table='<TABLE_NAME>', ids=primary_delete_ids)

# VAULT_ID1 will use credentials if you don't specify individual credentials at config level
response = skyflow_client.vault('VAULT_ID2').delete(primary_delete_request)


secondary_delete_ids = [
    'SKYFLOW_ID1',
    'SKYFLOW_ID2',
    'SKYFLOW_ID3',
]

secondary_delete_request = DeleteRequest(table='TABLE_NAME', ids=secondary_delete_ids)

# VAULT_ID2 will use individual credentials at config level
response = skyflow_client.vault('VAULT_ID2').delete(primary_delete_request)
