import asyncio

from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import BulkDetokenizeRequest


async def perform_bulk_detokenize_async():
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

        detokenize_request = BulkDetokenizeRequest(
            tokens=['<TOKEN_1>', '<TOKEN_2>'],
        )

        # Async variant -- batches are dispatched concurrently and awaited.
        response = await skyflow_client.vault(vault_config.get('vault_id')).bulk_detokenize_async(detokenize_request)

        print('Summary: ', response.summary)
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


asyncio.run(perform_bulk_detokenize_async())
