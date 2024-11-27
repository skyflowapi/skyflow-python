import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import GetRequest

"""
 * Skyflow Secure Column-Based Retrieval Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a column-based get request
 * 4. Handle response and errors
"""

def perform_secure_column_retrieval():
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
            'vault_id': '<VAULT_ID1>',      # primary vault
            'cluster_id': '<CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,                # Deployment environment (PROD by default)
            'credentials': credentials      # Authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)  # Used if no individual credentials are passed
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Column-Based Retrieval Data
        column_values = [
            '<VALUE1>', # Example Unique Column value 1
            '<VALUE2>'  # Example Unique Column value 2
        ]
        table_name = '<TABLE_NAME>'   # Replace with your actual table name
        column_name = '<COLUMN_NAME>' # Column name configured as unique in the schema

        # Step 5: Create Get Column Request
        get_request = GetRequest(
            table=table_name,
            column_name=column_name,
            column_values=column_values, # Column values of the records to return
            return_tokens=True           # Optional: Get tokens for retrieved data
        )

        # Step 6: Perform Secure Retrieval
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).get(get_request)

        # Handle Successful Response
        print('Column-based retrieval successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the secure column retrieval function
perform_secure_column_retrieval()
