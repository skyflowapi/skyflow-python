import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

"""
 * Skyflow Detokenization Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a detokenization request
 * 4. Handle response and errors
"""

def perform_detokenization():
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
            'token': '<YOUR_TOKEN>'  # Bearer token for authentication
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
            .add_skyflow_credentials(skyflow_credentials)  # Used if no individual credentials are passed
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 4: Prepare Detokenization Data
        detokenize_data = ['token1', 'token2', 'token3'] # Tokens to be detokenized
        redaction_type = RedactionType.REDACTED

        # Create Detokenize Request
        detokenize_request = DetokenizeRequest(
            tokens=detokenize_data,
            redaction_type=redaction_type,
            continue_on_error=True # Continue processing on errors
        )

        # Step 5: Perform Detokenization
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).detokenize(detokenize_request)

        # Handle Successful Response
        print('Detokenization successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the detokenization function
perform_detokenization()