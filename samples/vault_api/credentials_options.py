from skyflow.error import SkyflowError
from skyflow import Skyflow, LogLevel
from skyflow import Env
from skyflow.vault.data import DeleteRequest

"""
Skyflow Secure Data Deletion Example

This example demonstrates how to:
    1. Configure Skyflow client credentials
    2. Set up vault configuration
    3. Create and perform delete requests
    4. Handle response and errors
"""

def perform_secure_data_deletion():
    try:
        # Step 1: Configure Bearer Token Credentials
        credentials = {
            'token': '<BEARER_TOKEN>',  # bearer token
            # api_key: 'API_KEY', # API_KEY
            # path: 'PATH', # path to credentials file
            # credentials_string: 'your_credentials_string', # Credentials as string
        }

        # Step 2: Configure Vaults
        primary_vault_config = {
            'vault_id': '<VAULT_ID1>',  # primary vault
            'cluster_id': '<CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment (PROD by default)
        }

        secondary_vault_config = {
            'vault_id': 'VAULT_ID2',  # Secondary vault
            'cluster_id': 'CLUSTER_ID2',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment
            'credentials': credentials
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_vault_config(secondary_vault_config)
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Delete Request for Primary Vault
        primary_delete_ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>']

        primary_table_name = '<PRIMARY_TABLE_NAME>'  # Replace with actual table name

        primary_delete_request = DeleteRequest(
            table=primary_table_name,
            ids=primary_delete_ids
        )

        # Perform Delete Operation for Primary Vault
        primary_delete_response = skyflow_client.vault('<VAULT_ID>').delete(primary_delete_request)

        # Handle Successful Response
        print('Primary Vault Deletion Successful:', primary_delete_response)

        # Step 5: Prepare Delete Request for Secondary Vault
        secondary_delete_ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>']

        secondary_table_name = '<SECONDARY_TABLE_NAME>'  # Replace with actual table name

        secondary_delete_request = DeleteRequest(
            table=secondary_table_name,
            ids=secondary_delete_ids
        )

        # Perform Delete Operation for Secondary Vault
        secondary_delete_response = skyflow_client.vault('<SECONDARY_VAULT_ID>').delete(secondary_delete_request)

        #  Handle Successful Response
        print('Secondary Vault Deletion Successful:', secondary_delete_response)


    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the secure data deletion function
perform_secure_data_deletion()