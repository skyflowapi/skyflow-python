from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import RequestMethod
from skyflow.vault.connection import InvokeConnectionRequest

"""
 * Skyflow Connection Invocation Example
 * 
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault and connection configurations
 * 3. Invoke a connection
 * 4. Handle response and errors
"""

def invoke_skyflow_connection():
    try:
        # Step 1: Configure Credentials
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

        # Step 3: Configure Connection
        primary_connection_config = {
            'connection_id': '<YOUR_CONNECTION_ID>',   # Unique connection identifier
            'connection_url': '<YOUR_CONNECTION_URL>', # Connection url
            'credentials': credentials            # Connection-specific credentials
        }

        # Step 4: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_connection_config(primary_connection_config)
            .set_log_level(LogLevel.ERROR)  # Logging verbosity
            .build()
        )

        # Step 5: Prepare Connection Request
        request_body = {
            '<KEY1>': '<VALUE1>', # Replace with actual key-value pairs
            '<KEY2>': '<VALUE2>'
        }

        request_headers = {
            'Content-Type': 'application/json'
        }

        request_method = RequestMethod.POST

        # Step 6: Create Invoke Connection Request
        invoke_connection_request = InvokeConnectionRequest(
            method=request_method,
            body=request_body,
            headers=request_headers
        )

        # Step 7: Invoke Connection
        response = skyflow_client.connection().invoke(invoke_connection_request)

        # Handle Successful Response
        print('Connection invocation successful: ', response)

    except SkyflowError as error:
        # Comprehensive Error Handling
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the connection function
invoke_skyflow_connection()