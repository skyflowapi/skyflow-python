import base64

from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DataSourceType, DetectRunStatus
from skyflow.vault.detect import GetRunRequest

"""
 * Skyflow Get Run Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Retrieve the status and outputs of a file de-identification run
 * 4. Decode and save the outputs
 * 5. Handle response and errors
"""

def perform_get_run():
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

        # Step 4: Create the request with the run_id that deidentify_file returned
        request = GetRunRequest(run_id='<RUN_ID>')

        # Step 5: Get the run
        response = skyflow_client.detect(vault_config.get('vault_id')).get_run(request)

        print('Run ID:', response.run_id, 'Status:', response.status)
        if response.status == DetectRunStatus.SUCCESS and response.output_type == DataSourceType.BASE64:
            # get_run doesn't write files, so decode and save each output here
            for index, output in enumerate(response.output):
                extension = output.processed_file_extension.value if output.processed_file_extension else 'bin'
                with open(f'processed-{index}.{extension}', 'wb') as out_file:
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

# Invoke the get run function
perform_get_run()
