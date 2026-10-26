import base64

from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DataSourceType, DetectRunStatus, EntityType, FileDataFormat, RedactionType
from skyflow.vault.detect import ReidentifyFileRequest, RedactionLevel

"""
 * Skyflow Re-identify File Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Base64-encode a de-identified file and re-identify it
 * 4. Decode and save the re-identified file
 * 5. Handle response and errors
"""

def perform_reidentify_file():
    try:
        # Step 1: Configure Credentials
        credentials = {
            'path': '<PATH_TO_CREDENTIALS_JSON>'  # Path to your service account credentials file
        }

        # Step 2: Configure Vault
        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',  # Replace with your vault ID
            'cluster_id': '<YOUR_CLUSTER_ID>',  # Replace with your cluster ID
            'env': Env.PROD,  # Deployment environment
            'credentials': credentials
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        # Step 4: Encode the file; reidentify_file doesn't accept file or file_path
        with open('<PATH_TO_DEIDENTIFIED_FILE>', 'rb') as file_obj:
            encoded_file = base64.b64encode(file_obj.read()).decode('utf-8')

        request = ReidentifyFileRequest(
            data_source=DataSourceType.BASE64,
            value=encoded_file,
            data_format=FileDataFormat.TXT,  # txt, csv, json, xlsx, docx, pptx, xml, or jsonl
            redaction_level=[
                RedactionLevel(entity_name=EntityType.NAME, redaction_type=RedactionType.PLAIN_TEXT)
            ]
        )

        # Step 5: Re-identify the file; the response contains the result
        response = skyflow_client.detect(vault_config.get('vault_id')).reidentify_file(request)

        print('Status:', response.status)
        if response.status == DetectRunStatus.SUCCESS and response.output_type == DataSourceType.BASE64:
            # The SDK doesn't write the output, so decode and save it here
            for index, output in enumerate(response.output):
                extension = output.processed_file_extension.value if output.processed_file_extension else 'txt'
                with open(f'reidentified-{index}.{extension}', 'wb') as out_file:
                    out_file.write(base64.b64decode(output.processed_file))

    except SkyflowError as error:
        # Handle Skyflow-specific errors
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        # Handle unexpected errors
        print('Unexpected Error:', error)

# Invoke the re-identify file function
perform_reidentify_file()
