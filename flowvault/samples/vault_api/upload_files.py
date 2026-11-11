from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import UploadFilesRequest, UploadFilesRequestRecord, UploadFilesRequestColumn


def perform_upload_files():
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

        # Each column takes exactly ONE of file_path / base64 (needs file_name) / file_object.
        # Omit skyflow_id to create a new record; set it to upload into an existing record.
        upload_files_request = UploadFilesRequest(
            records=[
                UploadFilesRequestRecord(
                    table_name='<SENSITIVE_DATA_TABLE>',
                    columns=[
                        UploadFilesRequestColumn(column='<FILE_COLUMN>', file_path='<PATH_TO_FILE>'),
                    ],
                ),
            ],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).upload_files(upload_files_request)

        # response.records: list of UploadFilesResponseRecord, one per input record, in order.
        # Each has .skyflow_id, .table_name, .columns, .http_code, .error, .request_id.
        # Each column result has .column, .file_name, .upload_status ("UPLOADED"/"FAILED"/"SKIPPED"), .error.
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_upload_files()
