from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import DeleteRequest


def perform_secure_data_deletion():
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

        delete_request = DeleteRequest(
            table='<SENSITIVE_DATA_TABLE>',
            ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>'],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).delete(delete_request)

        # response.records (one entry per input, success + failure inline):
        #   {'skyflow_id': '<SKYFLOW_ID1>', 'http_code': 200, 'error': None}
        #   {'skyflow_id': None, 'http_code': 404, 'error': '<ERROR_MESSAGE>'}
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_deletion()
