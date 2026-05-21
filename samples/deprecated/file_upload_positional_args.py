import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import FileUploadRequest

"""
 * [DEPRECATED] Skyflow FileUploadRequest Positional Arguments Example
 *
 * Passing positional arguments after 'table' in FileUploadRequest is deprecated.
 * Use keyword arguments instead.
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Upload a file using the deprecated positional argument order
 * 4. Handle response and errors
 *
 * Migration:
 *   Before: FileUploadRequest(table, skyflow_id, column_name, file_object=file_obj)
 *   After:  FileUploadRequest(table, column_name=column_name, skyflow_id=skyflow_id, file_object=file_obj)
"""

def perform_file_upload_deprecated():
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

        # Step 4: Perform File Upload using deprecated positional argument order
        with open('<PATH_TO_FILE>', 'rb') as file_obj:
            # DEPRECATED: positional args after 'table' are deprecated.
            # Old order: (table, skyflow_id, column_name)
            # Use keyword arguments instead (see migration above).
            upload_request = FileUploadRequest(
                '<TABLE_NAME>',
                '<SKYFLOW_ID>',
                '<COLUMN_NAME>',
                file_object=file_obj
            )

            response = skyflow_client.vault('<YOUR_VAULT_ID>').upload_file(upload_request)
            print('File upload successful: ', response)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)

# Invoke the function
perform_file_upload_deprecated()
