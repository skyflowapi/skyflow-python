from skyflow_flowvault.error import SkyflowError
from skyflow_flowvault import Env
from skyflow_flowvault import Skyflow, LogLevel


# HTTP timeout and retry settings mirror Java's VaultConfig, at two levels:
#   - client-wide via builder methods (.timeout / .connect_timeout / .read_timeout /
#     .write_timeout / .max_retries / .initial_retry_delay_millis / .max_retry_delay_millis)
#   - per-vault via keys on the vault config dict (same names, plus 'vault_url')
# Precedence is resolved per field: per-vault -> client-wide -> SDK default.
#
#   timeout                     seconds, overall call ceiling incl. retries + backoff. Default 60.
#   connect_timeout             seconds, per-attempt connect. Default 10.
#   read_timeout                seconds, per-attempt response read. Default 10.
#   write_timeout               seconds, per-attempt request write. Default 10.
#   max_retries                 retry attempts after the first failure (408/429/5xx). Default 0 (off).
#   initial_retry_delay_millis  backoff before the first retry. Default 500.
#   max_retry_delay_millis      ceiling the exponential backoff grows to. Default 2000.
#   vault_url                   per-vault only; overrides the URL derived from cluster_id/env.
def perform_operation_with_timeout_and_retry():
    try:
        credentials = {
            'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>',
        }

        vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',
            'cluster_id': '<YOUR_CLUSTER_ID>',
            'env': Env.PROD,
            'credentials': credentials,
            # Per-vault overrides (win over the client-wide values below).
            'timeout': 30,
            'connect_timeout': 5,
            'read_timeout': 20,
            'write_timeout': 5,
            'max_retries': 2,
        }

        skyflow_client = (
            Skyflow.builder()
            # Client-wide defaults; any vault that doesn't override a field inherits these.
            .timeout(60)
            .connect_timeout(10)
            .read_timeout(15)
            .write_timeout(10)
            .max_retries(3)
            .initial_retry_delay_millis(500)
            .max_retry_delay_millis(4000)
            .add_vault_config(vault_config)
            .set_log_level(LogLevel.ERROR)
            .build()
        )

        print('Skyflow client configured with custom timeout & retry settings:', skyflow_client)

        # Use the client as usual; requests now fail fast at the configured timeouts and retry
        # transient 408/429/5xx responses with exponential backoff + jitter.
        # response = skyflow_client.vault(vault_config.get('vault_id')).bulk_detokenize(detokenize_request)
        # print(response.summary)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details,
        })
    except Exception as error:
        print('Unexpected Error:', error)


perform_operation_with_timeout_and_retry()
