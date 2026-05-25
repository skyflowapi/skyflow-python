import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

"""
 * [DEPRECATED] Skyflow Detokenize with 'redaction' Key Example
 *
 * The 'redaction' key in detokenize data is deprecated.
 * Use 'redaction_type' instead.
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Detokenize using the deprecated 'redaction' key
 * 4. Handle response and errors
 *
 * Migration:
 *   Before: {'token': '<TOKEN>', 'redaction': RedactionType.PLAIN_TEXT}
 *   After:  {'token': '<TOKEN>', 'redaction_type': RedactionType.PLAIN_TEXT}
"""

def perform_detokenization_deprecated():
    try:
        # Step 1: Configure Credentials
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',
            'clientName': '<YOUR_CLIENT_NAME>',
            'tokenURI': '<YOUR_TOKEN_URI>',
            'keyID': '<YOUR_KEY_ID>',
            'privateKey': '<YOUR_PRIVATE_KEY>',
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)
        }

        credentials = {
            'token': '<YOUR_TOKEN>'
        }

        # Step 2: Configure Vault
        primary_vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',
            'env': Env.PROD,
            'credentials': credentials
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        # Step 4: Prepare Detokenization Data using deprecated 'redaction' key
        # DEPRECATED: 'redaction' key will be removed in a future release.
        # Use 'redaction_type' instead (see migration above).
        detokenize_data = [
            {
                'token': '<TOKEN1>',
                'redaction': RedactionType.REDACTED
            },
            {
                'token': '<TOKEN2>',
                'redaction': RedactionType.MASKED
            }
        ]

        detokenize_request = DetokenizeRequest(
            data=detokenize_data,
            continue_on_error=True
        )

        # Step 5: Perform Detokenization
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).detokenize(detokenize_request)
        print('Detokenization successful: ', response)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the function
perform_detokenization_deprecated()
