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
 * 3. Create a file upload request
 * 4. Handle response and errors
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
            'vault_id': '<YOUR_VAULT_ID1>',
            'cluster_id': '<YOUR_CLUSTER_ID1>',
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

        # Step 4: Prepare File Upload Data
        with open('<PATH_TO_FILE>', 'rb') as file_obj:
            file_upload_request = FileUploadRequest(
                table='<TABLE_NAME>',  # Table to upload file to
                column_name='<COLUMN_NAME>',  # Column to upload file into
                file_object=file_obj,  # Pass file object
                skyflow_id='<SKYFLOW_ID>'  # Record ID to associate the file with
            )

            # Step 5: Perform File Upload
            response = skyflow_client.vault('<VAULT_ID>').upload_file(file_upload_request)

            # Handle Successful Response
            print('File upload successful: ', response)

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
