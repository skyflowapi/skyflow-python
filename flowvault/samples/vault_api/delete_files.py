from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import DeleteFilesRequest, DeleteFilesRequestRecord


def perform_delete_files():
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

        # Each record sets exactly ONE of skyflow_id or unique_values to target the record(s).
        delete_files_request = DeleteFilesRequest(
            records=[
                DeleteFilesRequestRecord(
                    table_name='<SENSITIVE_DATA_TABLE>',
                    columns=['<FILE_COLUMN>'],
                    skyflow_id='<SKYFLOW_ID>',
                ),
            ],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).delete_files(delete_files_request)

        # response.records: list of DeleteFilesResponseRecord, one per resolved record, in order.
        # Each has .skyflow_id, .table_name, .columns, .http_code, .error, .request_id.
        # Each column result has .column and .status ("DELETED"); .columns is None on a failed record.
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_delete_files()
