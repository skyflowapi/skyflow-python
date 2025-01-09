import json
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.error import SkyflowError
from skyflow.utils.enums import TokenMode
from skyflow.vault.data import InsertRequest

"""
 * Skyflow Insert with BYOT Example
 * 
 * This example demonstrates:
 * 1. Configuring Skyflow client credentials
 * 2. Setting up vault configuration
 * 3. Utilizing Bring Your Own Token (BYOT) during insertion
 * 4. Handling responses and errors
"""

def perform_secure_data_insertion_with_byot():
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
            'vault_id': '<YOUR_VAULT_ID1>',      # primary vault
            'cluster_id': '<YOUR_CLUSTER_ID1>',  # Cluster ID from your vault URL
            'env': Env.PROD,                # Deployment environment (PROD by default)
            'credentials': credentials      # Authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)  # Used if no individual credentials are passed
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

        table_name = '<SENSITIVE_DATA_TABLE>'

        #  Step 5: BYOT Configuration
        tokens = [
            {
                'card_number': '<TOKEN1>',
                'cvv': '<TOKEN2>',
            },
        ]

        insert_request = InsertRequest(
            table_name=table_name,
            values=insert_data,
            token_mode=TokenMode.ENABLE,  # Enable Bring Your Own Token (BYOT)
            tokens=tokens,                # Specify tokens to use for BYOT
            return_tokens=True,           # Optionally get tokens for inserted data
            continue_on_error=True        # Optionally continue on partial errors
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
perform_secure_data_insertion_with_byot()