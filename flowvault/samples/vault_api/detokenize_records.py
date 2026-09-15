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

        # response.records: list of DetokenizeResponseRecord, one per input, in order.
        # Each has .token, .value, .token_group_name, .metadata (DetokenizeResponseRecordMetadata
        # with .skyflow_id / .table_name), .http_code, .error, .request_id.
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
