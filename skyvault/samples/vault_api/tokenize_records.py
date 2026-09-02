import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.tokens import TokenizeRequest

"""
 * Skyflow Tokenization Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Tokenize sensitive data
 * 4. Handle response and errors
"""

def execute_tokenization():
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
            'credentials_string': json.dumps(cred)
        }

        credentials = {
            'api_key': '<YOUR_SKYFLOW_API_KEY>'  # Using API Key authentication
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

        # Step 4: Prepare Tokenization Data
        tokenize_values = [
            {'value': '<VALUE1>', 'column_group': '<COLUMN_GROUP>'},
            {'value': '<VALUE2>', 'column_group': '<COLUMN_GROUP>'},
        ]

        tokenize_request = TokenizeRequest(
            values=tokenize_values
        )

        # Step 5: Execute Tokenization
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).tokenize(tokenize_request)

        # Handle Successful Response
        print('Tokenization successful:', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the tokenization function
execute_tokenization()