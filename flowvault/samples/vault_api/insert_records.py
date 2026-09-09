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

        # response.records: list of InsertResponseRecord, one per input, in order.
        # Each has .skyflow_id, .table_name, .tokens (dict of column -> list of Token),
        # .hashed_data, .http_code, .error, .request_id.
        for record in response.records:
            if record.error is None:
                print(f"{record.skyflow_id} -> tokens={record.tokens}")
            else:
                print(f"failed ({record.http_code}): {record.error} [request_id={record.request_id}]")

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_insertion()
