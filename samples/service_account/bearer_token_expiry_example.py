import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import RedactionType
from skyflow.vault.tokens import DetokenizeRequest

"""
  * This example demonstrates how to configure and use the Skyflow SDK
  * to detokenize sensitive data stored in a Skyflow vault.
  * It includes setting up credentials, configuring the vault, and
  * making a detokenization request. The code also implements a retry
  * mechanism to handle unauthorized access errors (HTTP 401).
"""


def detokenize_data(skyflow_client, vault_id):
    try:
        # Creating a list of tokens to be detokenized
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

        # Building a detokenization request
        detokenize_request = DetokenizeRequest(
            data=detokenize_data,
            continue_on_error=False
        )

        # Sending the detokenization request and receiving the response
        response = skyflow_client.vault(vault_id).detokenize(detokenize_request)

        # Printing the detokenized response
        print('Detokenization successful:', response)

    except SkyflowError as error:
        print("Skyflow error occurred:", error)
        raise

    except Exception as error:
        print("Unexpected error occurred:", error)
        raise


def perform_detokenization():
    try:
        # Setting up credentials for accessing the Skyflow vault
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',
            'clientName': '<YOUR_CLIENT_NAME>',
            'tokenURI': '<YOUR_TOKEN_URI>',
            'keyID': '<YOUR_KEY_ID>',
            'privateKey': '<YOUR_PRIVATE_KEY>',
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)  # Credentials string for authentication
        }

        credentials = {
            'token': '<YOUR_TOKEN>'
        }

        # Configuring the Skyflow vault with necessary details
        primary_vault_config = {
            'vault_id': '<YOUR_VAULT_ID1>',      # Vault ID
            'cluster_id': '<YOUR_CLUSTER_ID1>',  # Cluster ID
            'env': Env.PROD,                     # Environment set to PROD
            'credentials': credentials           # Setting credentials
        }

        # Creating a Skyflow client instance with the configured vault
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)
            .set_log_level(LogLevel.ERROR)      # Setting log level to ERROR
            .build()
        )

        # Attempting to detokenize data using the Skyflow client
        try:
            detokenize_data(skyflow_client, primary_vault_config.get('vault_id'))
        except SkyflowError as err:
            # Retry detokenization if the error is due to unauthorized access (HTTP 401)
            if err.http_code == 401:
                print("Unauthorized access detected. Retrying...")
                detokenize_data(skyflow_client, primary_vault_config.get('vault_id'))
            else:
                # Rethrow the exception for other error codes
                raise err

    except SkyflowError as error:
        print('Skyflow Specific Error:', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the function
perform_detokenization()
