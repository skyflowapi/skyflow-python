from skyflow.error import SkyflowError
from skyflow import Skyflow, LogLevel
from skyflow import Env
from skyflow.vault.data import DeleteRequest

"""
Skyflow Secure Data Deletion Example

This example demonstrates how to:
    1. Configure Skyflow client credentials
    2. Set up vault configuration
    3. Create a delete request
    4. Handle response and errors
"""

def perform_secure_data_deletion():
    try:
        # Step 1: Configure Bearer Token Credentials
        credentials = {
            'token': '<BEARER_TOKEN>', # Bearer token
        }

        # Step 2: Configure vault
        primary_vault_config = {
            'vault_id': '<VAULT_ID1>',  # primary vault
            'cluster_id': '<CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment (PROD by default)
            'credentials': credentials,  # Authentication method
        }

        # Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(
                primary_vault_config
            )
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Add Secondary Vault Configuration

        secondary_vault_config = {
            'vault_id': 'VAULT_ID2',  # Secondary vault
            'cluster_id': 'CLUSTER_ID2',  # Cluster ID from your vault URL
            'env': Env.PROD,  # Deployment environment
            # If credentials aren't specified, Skyflow credentials will be used
        }

        # Add secondary vault config on the fly
        skyflow_client.add_vault_config(secondary_vault_config)

        # Step 5: Update Vault Configuration
        updated_vault_config = {
            'vault_id': 'VAULT_ID2', # Vault ID and cluster ID are unique
            'cluster_id': 'CLUSTER_ID2', # Cluster ID from your vault URL
            'credentials': credentials,  # Update credentials
        }

        # Update vault config on the fly
        skyflow_client.update_vault_config(updated_vault_config)

        # Step 6: Prepare Delete Request
        delete_ids = ['<SKYFLOW_ID1>', '<SKYFLOW_ID2>']

        table_name = '<TABLE_NAME>' # Replace with actual table name

        delete_request = DeleteRequest(
            table=table_name,
            ids=delete_ids
        )

        # Step 7: Perform Secure Deletion on Secondary Vault
        response = skyflow_client.vault('VAULT_ID2').delete(delete_request)

        # Handle Successful Response
        print('Delete successful: ', response)

        # Step 8: Remove Secondary Vault Configuration
        skyflow_client.remove_vault_config(secondary_vault_config.get('vault_id')) # Remove vault configuration

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the secure data deletion function
perform_secure_data_deletion()