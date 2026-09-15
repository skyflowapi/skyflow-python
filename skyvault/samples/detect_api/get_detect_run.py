from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import GetDetectRunRequest

"""
 * Skyflow Get Detect Run Example
 * 
 * This example demonstrates how to:
 * 1. Configure credentials
 * 2. Set up vault configuration
 * 3. Create a get detect run request
 * 4. Call getDetectRun to poll for file processing results
 * 5. Handle response and errors
"""

def perform_get_detect_run():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'path': '/path/to/credentials.json'  # Path to credentials file
        }

        # Step 2: Configure Vault
        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',  # Replace with your vault ID
            'cluster_id': '<YOUR_CLUSTER_ID>',  # Replace with your cluster ID
            'env': Env.PROD,  # Deployment environment
            'credentials': credentials
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.INFO)  # Use LogLevel.ERROR in production
            .build()
        )

        # Step 4: Create GetDetectRunRequest
        get_detect_run_request = GetDetectRunRequest(
            run_id='<RUN_ID_FROM_DEIDENTIFY_FILE>'  # Replace with the runId from deidentifyFile call
        )

        # Step 5: Call getDetectRun API
        response = skyflow_client.detect().get_detect_run(get_detect_run_request)

        # Handle Successful Response
        print("\nGet Detect Run Response:", response)

    except SkyflowError as error:
        # Handle Skyflow-specific errors
        print('\nSkyflow Error:', {
            'http_code': error.http_code,
            'grpc_code': error.grpc_code,
            'http_status': error.http_status,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        # Handle unexpected errors
        print('Unexpected Error:', error)
