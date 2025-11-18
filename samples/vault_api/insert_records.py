from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import InsertRequest

"""
 * Skyflow Secure Data Insertion Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create an insert request
 * 4. Handle response and errors
"""
def perform_secure_data_insertion():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'api_key': '<SKYFLOW_API_KEY>' # Using API Key authentication
        }

        # Step 2: Configure Vault
        primary_vault_config = {
            'vault_id': '<YOUR_VAULT_ID1>',  # primary vault
            'cluster_id': '<YOUR_CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment (PROD by default)
            'credentials': credentials  # Authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Insertion Data
        insert_data = [
            {
                'card_number': '<VALUE1>',
                'cvv': '<VALUE2>',
            },
        ]

        table_name = '<SENSITIVE_DATA_TABLE>' # Replace with your actual table name

        # Step 5: Create Insert Request
        insert_request = InsertRequest(
            table=table_name,
            values=insert_data,
            return_tokens=True, # Optional: Get tokens for inserted data
            continue_on_error=True # Optional: Continue on partial errors
        )

        # Step 6: Perform Secure Insertion
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).insert(insert_request)

        # Handle Successful Response
        print('Insertion Successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the secure data insertion function
perform_secure_data_insertion()