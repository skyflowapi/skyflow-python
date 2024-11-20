import json
from skyflow import Skyflow, LogLevel
from skyflow import Env
from skyflow.vault.data import DeleteRequest

# To generate Bearer Token from credentials string.
skyflow_credentials = {
    'clientID':'<YOUR_CLIENT_ID>',
    'clientName':'<YOUR_CLIENT_NAME>',
    'tokenURI':'<YOUR_TOKEN_URI>',
    'keyID':'<YOUR_KEY_ID>',
    'privateKey':'<YOUR_PRIVATE_KEY>'
}
credentials_string = json.dumps(skyflow_credentials)

# please pass one of api_key, token, credentials_string & path as credentials
credentials = {
    'token': '<BEARER_TOKEN>',
    #'credentials_string': credentials_string
}


skyflow_client = (
    Skyflow.builder()
    .add_vault_config({
           'vault_id': '<VAULT_ID1>', # primary vault
           'cluster_id': '<CLUSTER_ID1>', # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
           'env': Env.PROD, # Env by default it is set to PROD
           'credentials': credentials # individual credentials
    })
    .set_log_level(LogLevel.ERROR) # set log level by default it is set to ERROR
    .build()
)


# add vault config on the fly

skyflow_client.add_vault_config(
    {
        'vault_id': 'VAULT_ID2',      # secondary vault
        'cluster_id': 'CLUSTER_ID2',  # ID from your vault URL Eg https://{clusterId}.vault.skyflowapis.com
        'env': Env.PROD,  # Env by default it is set to PROD
        # if you don't specify individual credentials, skyflow credentials will be used
    }
)


skyflow_client.update_vault_config({
    'vault_id': 'VAULT_ID2',
    'cluster_id': 'CLUSTER_ID2',
    'credentials': credentials, # update credentials
})


# perform operations

delete_request = DeleteRequest(
    table='<TABLE_NAME>',
    ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>']
)

# perform delete call if you don't specify vault() it will return the first valid vault
response = skyflow_client.vault('VAULT_ID2').delete(delete_request)

# remove vault on the fly
skyflow_client.remove_vault_config('VAULT_ID')