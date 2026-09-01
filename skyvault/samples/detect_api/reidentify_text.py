from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectEntities
from skyflow.vault.detect import ReidentifyTextRequest

"""
 * Skyflow Text Re-identification Example
 * 
 * This example demonstrates how to:
 * 1. Configure credentials
 * 2. Set up vault configuration
 * 3. Create a reidentify text request
 * 4. Use all available options for reidentification
 * 5. Handle response and errors
"""

def perform_text_reidentification():
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
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        # Step 4: Prepare Sample Redacted Text
        redacted_text = "<REDACTED_TEXT_TO_REIDENTIFY>"  # Replace with your redacted text

        # Step 5: Create Reidentify Request
        reidentify_request = ReidentifyTextRequest(
            text=redacted_text,
            plain_text_entities=[DetectEntities.PHONE_NUMBER]
        )

        # Step 6: Perform Text Reidentification
        response = skyflow_client.detect().reidentify_text(reidentify_request)

        # Step 7: Handle Successful Response
        print("\nReidentify Text Response:", response)

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
