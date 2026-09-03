import asyncio
import uuid

from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import (
    BulkInsertRequest,
    BulkInsertRequestRecord,
    BulkInsertOptions,
    UpsertOptions,
    CustomHeaderKey,
)


# The interceptor runs once per batch, so a per-request value such as a request id is generated
# fresh for each outgoing call rather than reused across the whole bulk operation.
def make_request_id():
    request_id = str(uuid.uuid4())
    print('request id =>', request_id)
    return request_id


def add_custom_headers(context):
    # context.operation ("INSERT"/"DETOKENIZE"), context.batch_index, context.total_batches.
    # Available keys on CustomHeaderKey: SKYFLOW_ACCOUNT_ID (x-skyflow-account-id),
    # SKYFLOW_ACCOUNT_NAME (x-skyflow-account-name), REQUEST_ID_HEADER (x-request-id).
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, make_request_id())


async def perform_bulk_insert_with_custom_headers():
    try:
        credentials = {
            'token': '<BEARER_TOKEN>',
        }

        vault_config = {
            'vault_id': '<VAULT_ID>',
            'cluster_id': '<CLUSTER_ID>',
            'env': Env.DEV,
            'credentials': credentials,
        }

        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.DEBUG)
            .build()
        )

        insert_request = BulkInsertRequest(
            table_name='<TABLE_NAME>',
            upsert=UpsertOptions(unique_columns=['<UPSERT_COLUMN_NAME>']),
            records=[BulkInsertRequestRecord(data={'<YOUR_COLUMN_NAME>': '<YOUR_VALUE>'}) for _ in range(100)],
        )

        # Attach custom headers through the interceptor on the options object.
        options = BulkInsertOptions(interceptor=add_custom_headers)

        response = await skyflow_client.vault(vault_config.get('vault_id')).bulk_insert_async(insert_request, options)

        print('inserted:', response.summary.total_inserted, 'of', response.summary.total_records)
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


asyncio.run(perform_bulk_insert_with_custom_headers())
