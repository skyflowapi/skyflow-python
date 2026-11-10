from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import DeidentifyFileRequest, PollOptions
from skyflow.utils.enums import DetectRunStatus, DeidentifySourceType, DeidentifyFileDataFormat


def perform_deidentify_file_submit_only():
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

        request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',
            configuration_id='<CONFIGURATION_ID>',
        )

        response = skyflow_client.detect().deidentify_file(request)

        print(response.run_id)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


def perform_deidentify_file_poll():
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

        request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',
            configuration_id='<CONFIGURATION_ID>',
            poll_options=PollOptions(wait_time=120),
            output_directory='<OUTPUT_DIR>',
        )

        response = skyflow_client.detect().deidentify_file(request)

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


def perform_deidentify_file_presigned():
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

        request = DeidentifyFileRequest(
            data_source=DeidentifySourceType.PRESIGNED_URL,
            value='<PRESIGNED_URL>',
            data_format=DeidentifyFileDataFormat.PDF,
            configuration_id='<CONFIGURATION_ID>',
        )

        response = skyflow_client.detect().deidentify_file(request)

        print(response.run_id)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


if __name__ == '__main__':
    perform_deidentify_file_poll()
