import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import GetRequest

def perform_secure_data_retrieval():
    try:
        # Step 1: Configure Credentials
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',  # Client identifier
            'clientName': '<YOUR_CLIENT_NAME>',  # Client name
            'tokenURI': '<YOUR_TOKEN_URI>',  # Token URI
            'keyID': '<YOUR_KEY_ID>',  # Key identifier
            'privateKey': '<YOUR_PRIVATE_KEY>',  # Private key for authentication
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)  # Token credentials
        }

        credentials = {
            'path': '<PATH_TO_CREDENTIALS_JSON>'  # Path to credentials file
        }

        # Step 2: Configure Vault
        primary_vault_config = {
            'vault_id': '<VAULT_ID1>',  # primary vault
            'cluster_id': '<CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment (PROD by default)
            'credentials': credentials  # Authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)  # Used if no individual credentials are passed
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Retrieval Data

        get_ids = ['<SKYFLOW_ID1>', 'SKYFLOW_ID2']

        get_request = GetRequest(
            table='<SENSITIVE_DATA_TABLE>', # Replace with your actual table name
            ids=get_ids,
        )

        # Step 6: Configure Get Options
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).get(get_request)

        # Handle Successful Response
        print('Data retrieval successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the secure data retrieval function

perform_secure_data_retrieval()