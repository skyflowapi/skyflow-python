from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import BulkDetokenizeRequest, TokenGroupRedactions


def perform_bulk_detokenize():
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

        # Batch size and concurrency are configured via env vars / a .env file:
        #   DETOKENIZE_BATCH_SIZE (default 50, max 1000), DETOKENIZE_CONCURRENCY_LIMIT (default 1, max 10).
        # A single bulk call accepts at most 10,000 tokens.
        detokenize_request = BulkDetokenizeRequest(
            tokens=['<TOKEN_1>', '<TOKEN_2>'],
            # optional per-group redaction override:
            token_group_redactions=[TokenGroupRedactions(token_group_name='<TOKEN_GROUP_NAME>', redaction='MASKED')],
        )

        response = skyflow_client.vault(vault_config.get('vault_id')).bulk_detokenize(detokenize_request)

        # response.summary: total_tokens / total_detokenized / total_failed
        # response.records: one entry per input token, in order, each tagged with 'index':
        #   {'index': 0, 'request_id': None, 'value': '<VALUE>', 'token_group_name': '<GROUP>',
        #    'metadata': {...}, 'http_code': 200, 'token': '<TOKEN_1>', 'error': None}
        print('Summary: ', response.summary)
        print('Records: ', response.records)

        retry_tokens = response.tokens_to_retry()
        if retry_tokens:
            print(f'{len(retry_tokens)} token(s) worth retrying')

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_bulk_detokenize()
