from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import UpdateRequest


def perform_secure_data_update():
    try:
        credentials = {
            'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>',
        }

        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',
            'env': Env.PROD,
            'credentials': credentials,
        }

        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        update_request = UpdateRequest(
            records=[
                dict(skyflow_id='<SKYFLOW_ID>', data={'name': 'Jane Doe'}),
            ],
            table_name='<SENSITIVE_DATA_TABLE>',
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).update(update_request)

        # response.records: [{'request_index': 0, 'skyflow_id': '<SKYFLOW_ID>', 'name': '<TOKEN>'}, ...]
        # response.errors: [{'request_index': 0, 'error': '<ERROR_MESSAGE>', 'code': 404, 'request_id': '<REQUEST_ID>'}, ...]
        print('Records: ', response.records)
        print('Errors: ', response.errors)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_update()
