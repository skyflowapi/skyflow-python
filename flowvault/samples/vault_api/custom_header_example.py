import uuid

from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import (
    InsertRequest,
    InsertRequestRecord,
    InsertOptions,
    UpsertOptions,
    CustomHeaderKey,
)


def make_request_id():
    request_id = str(uuid.uuid4())
    print('request id =>', request_id)
    return request_id


def add_custom_headers(context):
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, make_request_id())


def perform_insert_with_custom_headers():
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

        insert_request = InsertRequest(
            table_name='<TABLE_NAME>',
            upsert=UpsertOptions(unique_columns=['<UPSERT_COLUMN_NAME>']),
            records=[InsertRequestRecord(data={'<YOUR_COLUMN_NAME>': '<YOUR_VALUE>'})],
        )

        options = InsertOptions(interceptor=add_custom_headers)

        response = skyflow_client.vault(vault_config.get('vault_id')).insert(insert_request, options)

        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_insert_with_custom_headers()
