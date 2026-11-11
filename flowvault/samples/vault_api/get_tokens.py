from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import GetTokensRequest, GetTokensRequestRecord


def perform_get_tokens():
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

        # One record per input value; only deterministic token groups are supported.
        get_tokens_request = GetTokensRequest(
            records=[
                GetTokensRequestRecord(value='john@example.com', token_group_name='<TOKEN_GROUP_NAME>'),
                GetTokensRequestRecord(value='jane@example.com', token_group_name='<TOKEN_GROUP_NAME>'),
            ],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).get_tokens(get_tokens_request)

        # response.records: list of GetTokensResponseRecord, one per input, in order.
        # Each has .value, .token_group_name, .token, .http_code, .error, .request_id.
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_get_tokens()
