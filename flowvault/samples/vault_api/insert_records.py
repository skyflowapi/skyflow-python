from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.utils.enums import UpsertType
from skyflow.vault.data import InsertRequest, InsertRequestRecord, UpsertOptions


def perform_secure_data_insertion():
    try:
        credentials = {
            'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>',  # or 'api_key' / 'token' / 'credentials_string'
        }

        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',  # from the vault URL: https://{cluster_id}.vault.skyflowapis.com
            'env': Env.PROD,                    # DEV, STAGE, SANDBOX, or PROD (default)
            'credentials': credentials,
        }

        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        # table_name/upsert are set at exactly ONE level -- on the request (applying to every
        # record) OR on every record individually, never both. upsert is an UpsertOptions object.
        records = [
            InsertRequestRecord(data={'name': 'John Doe', 'email': 'john@example.com'}),
            # InsertRequestRecord(
            #     data={'name': 'Jane Doe', 'email': 'jane@example.com'},
            #     table_name='<OTHER_TABLE>',  # per-record table override
            #     upsert=UpsertOptions(update_type=UpsertType.REPLACE, unique_columns=['email']),  # per-record upsert override
            # ),
        ]

        insert_request = InsertRequest(
            records=records,
            table_name='<SENSITIVE_DATA_TABLE>',
            upsert=UpsertOptions(update_type=UpsertType.UPDATE, unique_columns=['email']),
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).insert(insert_request)

        # response.records: [
        #   {'table_name': '<TABLE>', 'skyflow_id': '<SKYFLOW_ID>',
        #    'tokens': {'email': [{'token': '<TOKEN>', 'token_group_name': '<GROUP>', 'path': None}]},
        #    'hashed_data': {...}, 'http_code': 200, 'error': None},
        #   {'table_name': None, 'skyflow_id': None, 'tokens': None, 'hashed_data': None,
        #    'http_code': 400, 'error': '<ERROR_MESSAGE>'}
        # ]
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_insertion()
