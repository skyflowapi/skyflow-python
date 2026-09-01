# FlowVault Python samples

Runnable examples for the `skyflow-flowvault` SDK — one file per operation. See the
[flowvault README](../README.md) for the full SDK guide.

## Prerequisites

- Python 3.9+
- `pip install skyflow-flowvault`
- A Flow DB vault and Skyflow credentials (a service-account `credentials.json`, an API key, or a
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

For the bulk samples you can tune batching/concurrency via env vars or a `.env` file in the working
directory — e.g. `INSERT_BATCH_SIZE=100`, `INSERT_CONCURRENCY_LIMIT=5`.

## Run

```bash
python flowvault/samples/vault_api/insert_records.py
python flowvault/samples/vault_api/bulk_insert_async.py   # async samples run themselves via asyncio.run(...)
```

## Vault operations

| Sample | Demonstrates |
|---|---|
| [insert_records.py](vault_api/insert_records.py) | Insert records (request-level and per-record `table_name`/`upsert`) |
| [get_records.py](vault_api/get_records.py) | Retrieve records by Skyflow ID |
| [update_record.py](vault_api/update_record.py) | Update a record |
| [delete_records.py](vault_api/delete_records.py) | Delete records |
| [detokenize_records.py](vault_api/detokenize_records.py) | Detokenize tokens |
| [query_records.py](vault_api/query_records.py) | Run a SQL `SELECT` query |

## Bulk operations

Each bulk operation ships a **sync** and an **async** variant.

| Sample | Demonstrates |
|---|---|
| [bulk_insert_sync.py](vault_api/bulk_insert_sync.py) / [bulk_insert_async.py](vault_api/bulk_insert_async.py) | Batched, concurrent insert of many records; `summary`, per-record results, `records_to_retry()` |
| [bulk_detokenize_sync.py](vault_api/bulk_detokenize_sync.py) / [bulk_detokenize_async.py](vault_api/bulk_detokenize_async.py) | Batched, concurrent detokenize of many tokens; `tokens_to_retry()` |
