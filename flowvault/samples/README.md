# FlowVault Python samples

Runnable examples for the `skyflow-flowvault-python` SDK — one file per operation. See the
[flowvault README](../README.md) for the full SDK guide.

## Prerequisites

- Python 3.9+
- `pip install skyflow-flowvault-python`
- A FlowVault vault and Skyflow credentials (a service-account `credentials.json`, an API key, or a
  bearer token).

## Configure

Each sample has placeholders near the top — replace them with your own values:

```python
credentials = {'path': '<PATH_TO_YOUR_CREDENTIALS_JSON>'}   # or 'api_key' / 'token' / 'credentials_string'
vault_config = {
    'vault_id': '<YOUR_VAULT_ID>',
    'cluster_id': '<YOUR_CLUSTER_ID>',
    'env': Env.PROD,
    'credentials': credentials,
}
```

## Run

```bash
python flowvault/samples/vault_api/insert_records.py
```

## Vault operations

| Sample | Demonstrates |
|---|---|
| [insert_records.py](vault_api/insert_records.py) | Insert records (request-level and per-record `table_name`/`upsert`) |
| [get_records.py](vault_api/get_records.py) | Retrieve records by Skyflow ID |
| [update_record.py](vault_api/update_record.py) | Update a record |
| [delete_records.py](vault_api/delete_records.py) | Delete records |
| [detokenize_records.py](vault_api/detokenize_records.py) | Detokenize tokens |
| [query_records.py](vault_api/query_records.py) | Run a read-only SQL `SELECT` query |
| [get_tokens.py](vault_api/get_tokens.py) | Look up existing tokens for values (deterministic token groups) |
| [upload_files.py](vault_api/upload_files.py) | Upload files to file columns (`file_path` / `base64` / `file_object`) |
| [delete_files.py](vault_api/delete_files.py) | Delete files from file columns (by `skyflow_id` or `unique_values`) |

## Custom headers & HTTP config

| Sample | Demonstrates |
|---|---|
| [custom_header_example.py](vault_api/custom_header_example.py) | Attach custom headers via an `InsertOptions` interceptor (`CustomHeaderKey`) |
| [timeout_and_retry_config_example.py](vault_api/timeout_and_retry_config_example.py) | Per-vault `timeout` and `max_retries` config keys |

## Service account (token generation)

| Sample | Demonstrates |
|---|---|
| [bearer_token_generation_example.py](service_account/bearer_token_generation_example.py) | Bearer token from a credentials file path or a credentials string |
| [bearer_token_generation_with_context_example.py](service_account/bearer_token_generation_with_context_example.py) | Context-aware bearer tokens (string context and dict context) |
| [bearer_token_generation_using_threads_example.py](service_account/bearer_token_generation_using_threads_example.py) | Multithreaded token generation with a shared context |
| [scoped_token_generation_example.py](service_account/scoped_token_generation_example.py) | Scoped tokens via `role_ids` |
| [signed_token_generation_example.py](service_account/signed_token_generation_example.py) | Signed data tokens (`generate_signed_data_tokens`) |
