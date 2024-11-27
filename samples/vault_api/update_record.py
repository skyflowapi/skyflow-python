from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import UpdateRequest

"""
 * Skyflow Secure Data Update Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create an update request
 * 4. Handle response and errors
"""

def perform_secure_data_update():
    try:
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
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Update Data
        update_data = {
            'skyflow_id': '<SKYFLOW_ID>', # Skyflow ID of the record to update
            'card_number': '<VALUE>'      # Updated sensitive data
        }

        # Step 5: Create Update Request
        update_request = UpdateRequest(
            table='<SENSITIVE_DATA_TABLE>',
            data=update_data,
            return_tokens=True # Optional: Get tokens for updated data
        )

        # Step 7: Perform Secure Update
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).update(update_request)

        # Handle Successful Response
        print('Update successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the secure data update function
perform_secure_data_update()