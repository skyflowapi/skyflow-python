from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import DeidentifyFileRequest, GetRunRequest, PollOptions
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

        request = DeidentifyFileRequest(
            file_path='<PATH_TO_FILE>',
            configuration_id='<CONFIGURATION_ID>',
            poll_options=PollOptions(wait_time=64),
            output_directory='<OUTPUT_DIRECTORY>',
        )

        response = skyflow_client.detect().deidentify_file(request)

        print(response.run_id, response.status)
        if response.status == DetectRunStatus.SUCCESS:
            print(response.metrics.pages)
        elif response.status in (DetectRunStatus.IN_PROGRESS, DetectRunStatus.QUEUED):
            run = skyflow_client.detect().get_run(GetRunRequest(run_id=response.run_id))
            print(run.status)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })


if __name__ == '__main__':
    perform_deidentify_file()
