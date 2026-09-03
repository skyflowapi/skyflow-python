import asyncio

from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import BulkInsertRequest, BulkInsertRequestRecord, UpsertOptions


async def perform_bulk_multi_table_insert_async():
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

        # Multi-table mode: table_name is set on EVERY record instead of on the request.
        insert_request = BulkInsertRequest(
            records=[
                BulkInsertRequestRecord(
                    data={'<COLUMN_1>': '<VALUE_1>', '<COLUMN_2>': '<VALUE_2>'},
                    table_name='<YOUR_TABLE_NAME_1>',
                    upsert=UpsertOptions(unique_columns=['<COLUMN_1>']),
                ),
                BulkInsertRequestRecord(
                    data={'<COLUMN_1>': '<VALUE_1>', '<COLUMN_2>': '<VALUE_2>'},
                    table_name='<YOUR_TABLE_NAME_2>',
                ),
            ],
        )

        # Async variant -- batches are dispatched concurrently and awaited.
        response = await skyflow_client.vault(vault_config.get('vault_id')).bulk_insert_async(insert_request)

        print('inserted:', response.summary.total_inserted, 'of', response.summary.total_records)
        for record in response.records:
            if record.get('error') is None:
                print(f"[{record['index']}] {record.get('table_name')} -> skyflow_id={record.get('skyflow_id')}")
            else:
                print(f"[{record['index']}] failed ({record.get('http_code')}): {record.get('error')} "
                      f"[request_id={record.get('request_id')}]")

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


asyncio.run(perform_bulk_multi_table_insert_async())
