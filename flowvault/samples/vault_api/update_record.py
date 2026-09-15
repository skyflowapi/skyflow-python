from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import UpdateRequest, UpdateRequestRecord


def perform_secure_data_update():
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

        update_request = UpdateRequest(
            records=[
                UpdateRequestRecord(skyflow_id='<SKYFLOW_ID>', data={'name': 'Jane Doe'}),
            ],
            table_name='<SENSITIVE_DATA_TABLE>',
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).update(update_request)

        for record in response.records:
            if record.error is None:
                print(f"{record.skyflow_id} updated -> tokens={record.tokens}")
            else:
                print(f"{record.skyflow_id} failed ({record.http_code}): {record.error} "
                      f"[request_id={record.request_id}]")

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_data_update()
