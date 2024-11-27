import json
from skyflow.error import SkyflowError
from skyflow import Skyflow
from skyflow import LogLevel
from skyflow import Env
from skyflow.vault.data import DeleteRequest

"""
* Skyflow Delete Records Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a delete request
 * 4. Handle response and errors
"""

def perform_delete():
    try:
        # Step 1: Configure Credentials
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',       # Client identifier
            'clientName': '<YOUR_CLIENT_NAME>',   # Client name
            'tokenURI': '<YOUR_TOKEN_URI>',       # Token URI
            'keyID': '<YOUR_KEY_ID>',             # Key identifier
            'privateKey': '<YOUR_PRIVATE_KEY>',   # Private key for authentication
        }
        skyflow_credentials = {
            'credentials_string': json.dumps(cred) # Token credentials
        }

        credentials = {
            'api_key': '<YOUR_SKYFLOW_API_KEY>' # API key for authentication
        }

        # Step 2: Configure Vault
        primary_vault_config = {
            'vault_id': '<VAULT_ID1>',        # primary vault
            'cluster_id': '<CLUSTER_ID1>',    # Cluster ID from your vault URL
            'env': Env.PROD,                  # Deployment environment (PROD by default)
            'credentials': credentials        # Authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials) # Used if no individual credentials are passed
            .set_log_level(LogLevel.ERROR)                # Logging verbosity
            .build()
        )

        # Step 4: Prepare Delete Data
        delete_ids = ['SKYFLOW_ID1', 'SKYFLOW_ID2', 'SKYFLOW_ID3'] # Record IDs to delete
        table_name = '<SENSITIVE_DATA_TABLE>'

        # Create Delete Request
        delete_request = DeleteRequest(
            table=table_name,
            ids=delete_ids
        )

        # Step 5: Perform Deletion
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).delete(delete_request)

        # Handle Successful Response
        print('Deletion successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the deletion function
perform_delete()