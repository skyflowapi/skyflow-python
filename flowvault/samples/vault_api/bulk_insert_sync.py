from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import BulkInsertRequest, BulkInsertRecord, UpsertOptions
from skyflow_flowvault.utils.enums import UpsertType


def perform_bulk_insert():
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

        # Batch size and concurrency are configured via env vars / a .env file:
        #   INSERT_BATCH_SIZE (default 50, max 1000), INSERT_CONCURRENCY_LIMIT (default 1, max 10).
        # A single bulk call accepts at most 10,000 records.
        insert_request = BulkInsertRequest(
            table='<SENSITIVE_DATA_TABLE>',
            # upsert is optional; when present it sits at the same level as the table.
            upsert=UpsertOptions(unique_columns=['email'], update_type=UpsertType.UPDATE),
            records=[
                BulkInsertRecord(data={'name': 'John Doe', 'email': 'john@example.com'}),
                BulkInsertRecord(data={'name': 'Jane Doe', 'email': 'jane@example.com'}),
            ],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).bulk_insert(insert_request)

        # response.summary: total_records / total_inserted / total_failed
        # response.records: one entry per input, in order, each tagged with 'index':
        #   {'index': 0, 'request_id': None, 'table_name': '<TABLE>', 'skyflow_id': '<ID>',
        #    'tokens': {...}, 'data': {...}, 'hashed_data': {...}, 'http_code': 200, 'error': None}
        print('Summary: ', response.summary)
        print('Records: ', response.records)

        # Only server-side (5xx, excl. 529) failures are worth retrying:
        retry = response.records_to_retry()
        if retry:
            print(f'{len(retry)} record(s) worth retrying')

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_bulk_insert()
