# Skyflow FlowVault Python SDK

`skyflow-flowvault` is the Skyflow Python SDK built for **Flow DB** vaults. It shares its client,
credentials, and configuration with the [skyvault SDK](../skyvault/README.md) (both depend on the
`common` module) but exposes its own surface: **unary** vault operations plus **bulk** (batched,
concurrent) insert and detokenize.

> **`skyflow-flowvault` is versioned independently of `skyflow`.** It launched at `1.0.0` while
> `skyflow` is at `2.x`. The two are separate artifacts on separate version lines and cannot be
> installed into the same Python environment at once.

## Table of Contents

- [Overview](#overview)
- [Install](#install)
- [Quickstart](#quickstart)
- [Authenticate](#authenticate)
- [Initialize the client](#initialize-the-client)
- [Unary operations](#unary-operations)
  - [Insert](#insert) · [Get](#get) · [Update](#update) · [Delete](#delete) · [Detokenize](#detokenize) · [Query](#query)
- [Bulk operations](#bulk-operations)
  - [Bulk insert](#bulk-insert) · [Bulk detokenize](#bulk-detokenize)
  - [Batching and concurrency](#batching-and-concurrency)
- [Error handling](#error-handling)
- [Logging](#logging)
- [Samples](#samples)
- [Request / response shapes](#request--response-shapes)

## Overview

- Authenticate with a Skyflow service account, an API key, or a bearer token.
- Perform **unary** operations — insert, get, update, delete, detokenize, query.
- Perform **bulk** operations — insert and detokenize — each with a synchronous and an async
  variant, built for high-throughput Flow DB workloads.
- **Per-record reporting, not all-or-nothing.** A call succeeds as a call even when individual
  records fail; each response reports the outcome of every record (its own `http_code` and `error`).

## Install

```bash
pip install skyflow-flowvault
```

Requirements: **Python 3.9+**.

## Quickstart

```python
from skyflow_flowvault import Skyflow, LogLevel, Env
from skyflow_flowvault.vault.data import InsertRequest, InsertRequestRecord

credentials = {'api_key': '<API_KEY>'}  # or 'token' / 'path' / 'credentials_string'

vault_config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',   # from the vault URL: https://{cluster_id}.vault.skyflowapis.com
    'env': Env.PROD,                # DEV, STAGE, SANDBOX, or PROD (default)
    'credentials': credentials,
}

skyflow_client = (
    Skyflow.builder()
    .add_vault_config(vault_config)
    .set_log_level(LogLevel.ERROR)  # default is ERROR
    .build()
)

vault = skyflow_client.vault('<VAULT_ID>')

response = vault.insert(InsertRequest(
    table_name='cards',
    records=[InsertRequestRecord(data={'card_number': '4111111111111111'})],
))
print(response.records)
```

## Authenticate

Requests are authorized with Skyflow credentials attached to the vault config's `credentials` dict.
Set **exactly one** of:

| Key | What it is |
|---|---|
| `api_key` | A long-lived API key. Simplest option. |
| `token` | A short-lived bearer token you generate yourself. |
| `path` | Filesystem path to a service-account `credentials.json` — the SDK generates and refreshes tokens. |
| `credentials_string` | The contents of a `credentials.json` as a string — use when it comes from a secret store. |

Credentials resolve **most specific first**: per-vault (`vault_config['credentials']`) → client-wide
(`Skyflow.builder().add_skyflow_credentials(...)`) → the `SKYFLOW_CREDENTIALS` environment variable.

## Initialize the client

Build the client once and keep it for your application's lifetime; get a controller from it with
`vault(...)`.

```python
vault_config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',
    'env': Env.PROD,
    'credentials': {'path': '<PATH_TO_CREDENTIALS_JSON>'},
}

skyflow_client = Skyflow.builder().add_vault_config(vault_config).build()
vault = skyflow_client.vault('<VAULT_ID>')
```

## Unary operations

Every unary response is a single **`records`** list — success and failure inline, one entry per
input, each carrying its own `http_code` and `error`. Exact JSON for each is in
[CONTRACT_SHAPES.md](CONTRACT_SHAPES.md).

### Insert

`table_name`/`upsert` go at **exactly one** level — on the request (applies to all records) or on
every record — never both. `upsert` is an `UpsertOptions`; `tokens` is optional BYOT.

```python
from skyflow_flowvault.vault.data import InsertRequest, InsertRequestRecord, UpsertOptions
from skyflow_flowvault.utils.enums import UpsertType

request = InsertRequest(
    table_name='cards',
    upsert=UpsertOptions(unique_columns=['card_number'], update_type=UpsertType.UPDATE),
    records=[InsertRequestRecord(data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'})],
)
response = vault.insert(request)
for r in response.records:
    print(r['index'] if 'index' in r else '', r['skyflow_id'], r['tokens'], r['http_code'], r['error'])
```
Each record: `{table_name, skyflow_id, tokens, hashed_data, http_code, error}` (no plaintext `data`).

### Get

Two mutually exclusive modes — single-table, or multi-table via `records=[GetRecordRequest(...)]`.
`column_redactions` entries are `ColumnRedaction` objects.

```python
from skyflow_flowvault.vault.data import GetRequest, GetRecordRequest, ColumnRedaction

# single-table
vault.get(GetRequest(
    table='persons', ids=['<SKYFLOW_ID>'], columns=['name', 'email'],
    column_redactions=[ColumnRedaction(column_name='email', redaction='MASKED')],
))

# multi-table batch
vault.get(GetRequest(records=[
    GetRecordRequest(table='persons', ids=['<SKYFLOW_ID>'], columns=['name']),
    GetRecordRequest(table='cards', unique_values=[{'email': 'john@example.com'}]),
]))
```
Each record: `{table_name, skyflow_id, tokens, data, hashed_data, http_code, error}`.

### Update

```python
from skyflow_flowvault.vault.data import UpdateRequest

vault.update(UpdateRequest(
    table_name='persons',
    records=[{'skyflow_id': '<SKYFLOW_ID>', 'data': {'name': 'Jane'}}],
))
```

### Delete

```python
from skyflow_flowvault.vault.data import DeleteRequest

vault.delete(DeleteRequest(table='persons', ids=['<SKYFLOW_ID>']))
```
Each record: `{skyflow_id, http_code, error}`.

### Detokenize

```python
from skyflow_flowvault.vault.data import DetokenizeRequest

vault.detokenize(DetokenizeRequest(
    tokens=['<TOKEN>'],
    token_group_redactions=[{'token_group_name': 'card_number_cg', 'redaction': 'MASKED'}],
))
```
Each record: `{token, token_group_name, value, metadata, http_code, error}`.

### Query

```python
from skyflow_flowvault.vault.data import QueryRequest

response = vault.query(QueryRequest(query="SELECT * FROM persons WHERE skyflow_id = '<SKYFLOW_ID>'"))
print(response.records)    # [{'data': {...}}, ...]
print(response.metadata)   # {'columns': [...]}
```

## Bulk operations

Bulk operations split the payload into batches sent **concurrently** and return a **`summary`** plus
a **`records`** list — one entry per submitted item, in input order, each tagged with its `index`.
A single bulk call accepts at most **10,000** items.

### Bulk insert

```python
from skyflow_flowvault.vault.data import BulkInsertRequest, BulkInsertRecord

request = BulkInsertRequest(table='cards', records=[
    BulkInsertRecord(data={'card_number': '4111111111111111'}),
    BulkInsertRecord(data={'card_number': '4222222222222222'}),
])

response = vault.bulk_insert(request)                 # synchronous
# response = await vault.bulk_insert_async(request)   # async variant

print(response.summary.total_records, response.summary.total_inserted, response.summary.total_failed)
for r in response.records:
    print(r['index'], r['skyflow_id'], r['http_code'], r['error'])

retry = response.records_to_retry()   # original records whose http_code is 500-599 (excl. 529)
```
> `BulkInsertRecord` uses the field name `table` (not `table_name`) and has no `tokens` field.

### Bulk detokenize

```python
from skyflow_flowvault.vault.data import BulkDetokenizeRequest

request = BulkDetokenizeRequest(tokens=['<TOKEN_1>', '<TOKEN_2>'])

response = vault.bulk_detokenize(request)                 # synchronous
# response = await vault.bulk_detokenize_async(request)   # async variant

retry_tokens = response.tokens_to_retry()
```

### Batching and concurrency

Batch size and concurrency are configured **per operation** via environment variables, read from the
process environment first, then from a `.env` file in the working directory (via `python-dotenv`).

| Operation | Batch size var | Default | Max | Concurrency var | Default | Max |
|---|---|---|---|---|---|---|
| Bulk insert | `INSERT_BATCH_SIZE` | 50 | 1000 | `INSERT_CONCURRENCY_LIMIT` | 1 | 10 |
| Bulk detokenize | `DETOKENIZE_BATCH_SIZE` | 50 | 1000 | `DETOKENIZE_CONCURRENCY_LIMIT` | 1 | 10 |

Resolution: `batch_size = min(value, max)`; `concurrency = min(value, max, ceil(item_count / batch_size))`
— concurrency never exceeds the number of batches. Invalid values log a warning and fall back to the
default. The 10,000-item ceiling per call is fixed and not configurable.

```dotenv
# .env
INSERT_BATCH_SIZE=100
INSERT_CONCURRENCY_LIMIT=5
```

Merging is by input order regardless of which batch finishes first, so `index` always matches an
item's position in your submitted payload. A per-batch failure only fails that batch's records.

## Error handling

Two layers:

- **Request-level** — the call could not be made or wholly failed (invalid request, missing
  credentials, auth failure, over the 10,000 ceiling): raised as a `SkyflowError`.
- **Record-level** — the call succeeded but individual records failed: returned in the response.
  **Nothing is raised.** Each entry in `records` reports its own `http_code` and `error`.

```python
from skyflow_flowvault.error import SkyflowError

try:
    response = vault.bulk_insert(request)   # reaching here means the CALL succeeded
    for r in response.records:
        if r['error'] is not None:
            print('row', r['index'], 'failed', r['http_code'], r['error'])
except SkyflowError as e:
    print(e.http_code, e.message, e.details)
```

## Logging

The SDK logs at `LogLevel.ERROR` by default. Change it with
`Skyflow.builder().set_log_level(LogLevel.INFO)` (`DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`). The
batching warnings above are emitted at `WARN`.

## Samples

Runnable examples live in [samples/](samples/) — one file per operation, with sync/async pairs for
the bulk ops. See [samples/README.md](samples/README.md) to run them.

## Request / response shapes

[CONTRACT_SHAPES.md](CONTRACT_SHAPES.md) documents the exact request and response JSON for every
operation (unary and bulk), for reference and comparison against the Java FlowDB contract.
