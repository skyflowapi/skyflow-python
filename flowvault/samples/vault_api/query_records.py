from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel
from skyflow_flowvault.vault.data import QueryRequest


def perform_secure_query():
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

        query_request = QueryRequest(
            query="SELECT * FROM <SENSITIVE_DATA_TABLE> WHERE skyflow_id = '<SKYFLOW_ID>'",
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).query(query_request)

        # response.records: [{'data': {'skyflow_id': '<ID>', 'name': 'John Doe', 'email': '<TOKEN>'}}, ...]
        # response.metadata: {'columns': ['skyflow_id', 'name', 'email']}
        print('Records: ', response.records)
        print('Metadata: ', response.metadata)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_secure_query()
