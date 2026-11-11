from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import DeidentifyFileRequest, PollOptions
from skyflow.utils.enums import DetectRunStatus


def perform_deidentify_file():
    try:
        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',
            'env': Env.PROD,
            'credentials': {'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>'},
        }

        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        submit_request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',
            configuration_id='<CONFIGURATION_ID>',
        )

        submitted = skyflow_client.detect().deidentify_file(submit_request)

        print(submitted.run_id)

        poll_request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',
            configuration_id='<CONFIGURATION_ID>',
            poll_options=PollOptions(wait_time=120),
            output_directory='<OUTPUT_DIR>',
        )

        response = skyflow_client.detect().deidentify_file(poll_request)

        if response.status == DetectRunStatus.SUCCESS:
            for output in response.output:
                print(output.processed_file_type, output.processed_file_extension)
        elif response.status == DetectRunStatus.FAILED:
            print(response.message)
        else:
            print(response.run_id)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


if __name__ == '__main__':
    perform_deidentify_file()
