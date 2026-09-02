from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import BulkInsertRequest, BulkInsertRequestRecord, UpsertOptions


def perform_bulk_multi_table_insert():
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
        # The SDK rejects a request that sets it at both levels, or on only some of the records.
        insert_request = BulkInsertRequest(
            records=[
                BulkInsertRequestRecord(
                    data={'<COLUMN_1>': '<VALUE_1>', '<COLUMN_2>': '<VALUE_2>'},
                    table_name='<YOUR_TABLE_NAME_1>',
                    # upsert is optional; when update_type is omitted the vault treats it as UPDATE.
                    upsert=UpsertOptions(unique_columns=['<COLUMN_1>']),
                ),
                BulkInsertRequestRecord(
                    data={'<COLUMN_1>': '<VALUE_1>', '<COLUMN_2>': '<VALUE_2>'},
                    table_name='<YOUR_TABLE_NAME_2>',
                ),
            ],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).bulk_insert(insert_request)

        print('inserted:', response.summary.total_inserted, 'of', response.summary.total_records)
        for record in response.records:
            if record.get('error') is None:
                print(f"[{record['index']}] {record.get('table_name')} -> skyflow_id={record.get('skyflow_id')}")
            else:
                print(f"[{record['index']}] failed ({record.get('http_code')}): {record.get('error')} "
                      f"[request_id={record.get('request_id')}]")

        # Retry the records that failed with a retryable status (5xx other than 529). Each returned
        # record still carries its own table_name/upsert, so the retry needs no request-level table.
        records_to_retry = response.records_to_retry()
        if records_to_retry:
            retry_response = skyflow_client.vault(vault_config.get('vault_id')).bulk_insert(
                BulkInsertRequest(records=records_to_retry)
            )
            print('retry response:', retry_response.summary)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_bulk_multi_table_insert()
