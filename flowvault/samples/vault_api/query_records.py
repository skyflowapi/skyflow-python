from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import QueryRequest


def perform_query():
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

        # Only SELECT is supported; a call returns at most 25 records -- page with OFFSET.
        query_request = QueryRequest(
            query="SELECT name, email FROM <SENSITIVE_DATA_TABLE> LIMIT 25",
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).query(query_request)

        # response.records: list of QueryResponseRecord, each with .data (a dict of column -> value).
        # response.metadata.columns lists the returned columns; response.request_id is always set.
        print('Request ID: ', response.request_id)
        print('Columns: ', response.metadata.columns if response.metadata else None)
        print('Records: ', response.records)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_query()
