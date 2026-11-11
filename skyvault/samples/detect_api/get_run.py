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

        request = GetRunRequest(run_id='<RUN_ID>')

        run = skyflow_client.detect().get_run(request)

        if run.status == DetectRunStatus.SUCCESS:
            for output in run.output:
                print(output.processed_file_type, output.processed_file_extension)
        elif run.status == DetectRunStatus.FAILED:
            print(run.message)
        else:
            print(run.status)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
            'request_id': error.request_id,
        })


if __name__ == '__main__':
    perform_get_run()
