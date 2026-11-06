from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import EntityType, RedactionType
from skyflow.vault.detect import ReidentifyStringRequest, RedactionLevel

"""
 * Skyflow Re-identify String Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Re-identify de-identified text, choosing how each entity type displays
 * 4. Handle response and errors
"""

def perform_reidentify_string():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'path': '<PATH_TO_CREDENTIALS_JSON>'  # Path to your service account credentials file
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

        # Step 4: Create the request
        request = ReidentifyStringRequest(
            text='<DEIDENTIFIED_TEXT>',  # Text returned by deidentify_string
            redaction_level=[
                RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT),  # Reveal
                RedactionLevel(entity_name=EntityType.EMAIL_ADDRESS, redaction_type=RedactionType.MASKED)  # Mask
            ]
        )

        # Step 5: Re-identify the text
        response = skyflow_client.detect(vault_config.get('vault_id')).reidentify_string(request)

        print('Re-identified text:', response.processed_text)

    except SkyflowError as error:
        # Handle Skyflow-specific errors
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        # Handle unexpected errors
        print('Unexpected Error:', error)

# Invoke the re-identify string function
perform_reidentify_string()
