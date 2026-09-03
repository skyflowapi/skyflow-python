from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import DetokenizeRequest


def perform_secure_detokenization():
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

        detokenize_request = DetokenizeRequest(
            tokens=['<TOKEN1>', '<TOKEN2>'],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).detokenize(detokenize_request)

        # response.records (one entry per input, success + failure inline):
        #   {'token': '<TOKEN1>', 'token_group_name': '<GROUP>', 'value': '<VALUE>',
        #    'metadata': {'skyflow_id': '<ID>', 'table_name': '<TABLE>'}, 'http_code': 200, 'error': None}
        #   {'token': '<TOKEN2>', ..., 'http_code': 404, 'error': '<ERROR_MESSAGE>'}
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_detokenization()
