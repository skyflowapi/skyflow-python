import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import QueryRequest

"""
 * Skyflow Query Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Execute a query on the vault
 * 4. Handle response and errors
"""
def execute_query():
    try:
        # Step 1: Configure Credentials
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',     # Client identifier
            'clientName': '<YOUR_CLIENT_NAME>', # Client name
            'tokenURI': '<YOUR_TOKEN_URI>',     # Token URI
            'keyID': '<YOUR_KEY_ID>',           # Key identifier
            'privateKey': '<YOUR_PRIVATE_KEY>', # Private key for authentication
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)
        }

        credentials = {
            'api_key': '<SKYFLOW_API_KEY>' # Using API Key authentication
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
            .add_skyflow_credentials(skyflow_credentials) # Used if no individual credentials are passed
            .set_log_level(LogLevel.ERROR)                # Logging verbosity
            .build()
        )

        # Step 4: Prepare Query
        query = 'select * from table_name limit 1' # Example query

        query_request = QueryRequest(
            query=query
        )

        # Step 5: Execute Query
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).query(query_request)

        # Handle Successful Response
        print('Query Result: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the query function
execute_query()