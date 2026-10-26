from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.utils.enums import DetectRunStatus
from skyflow.vault.detect import DeidentifyFileRequest, PollOptions

"""
 * Skyflow De-identify File Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Submit a local file for de-identification and poll for the result
 * 4. Write the processed files to an output directory
 * 5. Handle response and errors
"""

def perform_deidentify_file():
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

        # Step 4: Create the request
        # Without poll_options, deidentify_file only submits the run and returns its run_id.
        # With poll_options, the SDK polls until the run finishes or a polling limit is reached.
        request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',  # Local file to de-identify
            configuration_id='<CONFIGURATION_ID>',  # ID of an existing Detect configuration
            poll_options=PollOptions(
                wait_time=120,  # Maximum total wait in seconds (1-300, default 60)
                max_attempts=10  # Maximum status checks (1-23, default 23)
            ),
            output_directory='<OUTPUT_DIRECTORY>'  # Where processed files are written; requires poll_options
        )

        # Step 5: De-identify the file
        response = skyflow_client.detect(vault_config.get('vault_id')).deidentify_file(request)

        print('Run ID:', response.run_id, 'Status:', response.status)
        if response.status == DetectRunStatus.SUCCESS:
            # The SDK has written each output to output_directory with a 'processed-' prefix
            for output in response.output:
                print(output.processed_file_type, output.processed_file_extension)
        elif response.status in (DetectRunStatus.QUEUED, DetectRunStatus.IN_PROGRESS):
            print('Still running. Call get_run later with run ID:', response.run_id)
        else:
            print('Run ended with status:', response.status, response.message)

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

# Invoke the de-identify file function
perform_deidentify_file()
