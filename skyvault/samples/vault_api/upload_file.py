import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import FileUploadRequest

"""
 * Skyflow File Upload Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Upload a file to an existing record (with skyflow_id)
 * 4. Upload a file and create a new record (without skyflow_id)
 * 5. Handle response and errors
 *
 * Note: All FileUploadRequest parameters must be
 * passed as keyword arguments.
"""

def perform_file_upload():
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

        # Step 4a: Upload a file to an existing record
        with open('<PATH_TO_FILE>', 'rb') as file_obj:
            upload_request = FileUploadRequest(
                table='<TABLE_NAME>',
                column_name='<COLUMN_NAME>',
                skyflow_id='<SKYFLOW_ID>',
                file_object=file_obj
            )

            response = skyflow_client.vault('<YOUR_VAULT_ID>').upload_file(upload_request)
            print('File upload to existing record:', response)

        # Step 4b: Upload a file and create a new record (omit skyflow_id)
        with open('<PATH_TO_FILE>', 'rb') as file_obj:
            upload_request = FileUploadRequest(
                table='<TABLE_NAME>',
                column_name='<COLUMN_NAME>',
                file_object=file_obj
            )

            response = skyflow_client.vault('<YOUR_VAULT_ID>').upload_file(upload_request)
            print('File upload with new record:', response)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the file upload function
perform_file_upload()
