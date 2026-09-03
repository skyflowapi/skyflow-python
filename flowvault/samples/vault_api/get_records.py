from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import GetRequest


def perform_secure_data_retrieval():
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

        get_request = GetRequest(
            table_name='<SENSITIVE_DATA_TABLE>',
            ids=['<SKYFLOW_ID1>', '<SKYFLOW_ID2>'],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).get(get_request)

        # response.records (one entry per input, success + failure inline):
        #   {'table_name': 'persons', 'skyflow_id': '<ID>', 'tokens': {...}, 'data': {...},
        #    'hashed_data': {...}, 'http_code': 200, 'error': None}
        #   {'table_name': None, 'skyflow_id': None, ..., 'http_code': 404, 'error': 'Record not found'}
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_retrieval()
