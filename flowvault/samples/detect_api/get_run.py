from skyflow.error import SkyflowError
from skyflow import Env, Skyflow, LogLevel
from skyflow.vault.detect import GetRunRequest
from skyflow.utils.enums import DetectRunStatus


def perform_get_run():
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

        response = skyflow_client.detect().get_run(GetRunRequest(run_id='<RUN_ID>'))

        print(response.run_id, response.status)
        if response.status == DetectRunStatus.SUCCESS:
            for output in response.output:
                print(output.processed_file_type, output.processed_file_extension)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })


if __name__ == '__main__':
    perform_get_run()
