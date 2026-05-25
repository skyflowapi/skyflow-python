import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel

"""
 * [DEPRECATED] Skyflow update_log_level Example
 *
 * update_log_level() is deprecated. Use set_log_level() instead.
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Change the log level at runtime using the deprecated update_log_level()
 * 4. Handle response and errors
 *
 * Migration:
 *   Before: skyflow_client.update_log_level(LogLevel.INFO)
 *   After:  skyflow_client.set_log_level(LogLevel.INFO)
"""

def perform_update_log_level():
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

        # Step 4: Change log level at runtime using deprecated method
        # DEPRECATED: update_log_level() will be removed in a future release.
        # Use set_log_level() instead.
        skyflow_client.update_log_level(LogLevel.INFO)

        print('Log level updated successfully (deprecated). Use set_log_level() instead.')

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the function
perform_update_log_level()
