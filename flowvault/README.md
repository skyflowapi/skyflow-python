# Skyflow FlowVault Python SDK

`skyflow-flowvault-python` is the Skyflow Python SDK built for **Flow DB** vaults. It shares its client,
credentials, and configuration with the [skyvault SDK](../skyvault/README.md) (both depend on the
`common` module) but exposes its own surface: **unary** vault operations plus **bulk** (batched,
concurrent) insert and detokenize.

> **Install name vs. import name.** You `pip install skyflow-flowvault-python`, then `import skyflow` —
> the same import name the `skyflow` (Privacy DB) SDK uses. The two are separate artifacts and **cannot
> be installed into the same Python environment at once** (they'd collide on the `skyflow` package).

## Table of Contents

- [Overview](#overview)
- [Install](#install)
- [Quickstart](#quickstart)
- [Authenticate](#authenticate)
- [Initialize the client](#initialize-the-client)
- [Timeouts and retries](#timeouts-and-retries)
- [Unary operations](#unary-operations)
  - [Insert](#insert) · [Get](#get) · [Update](#update) · [Delete](#delete) · [Detokenize](#detokenize) · [Query](#query)
- [Bulk operations](#bulk-operations)
  - [Bulk insert](#bulk-insert) · [Bulk detokenize](#bulk-detokenize)
  - [Batching and concurrency](#batching-and-concurrency)
  - [Custom request headers](#custom-request-headers)
- [Error handling](#error-handling)
- [Logging](#logging)
- [Samples](#samples)

## Overview

- Authenticate with a Skyflow service account, an API key, or a bearer token.
- Perform **unary** operations — insert, get, update, delete, detokenize, query.
- Perform **bulk** operations — insert and detokenize — each with a synchronous and an async
  variant, built for high-throughput Flow DB workloads.
- **Unary calls raise on failure; bulk calls report per-record.** A unary API error raises a
  `SkyflowError` with the server's details; a bulk call reports every record's outcome inline (its
  own `http_code` and `error`) so one bad record or batch never sinks the whole call.

## Install

```bash
pip install skyflow-flowvault-python
```

Requirements: **Python 3.9+**.

## Quickstart

```python
from skyflow import Skyflow, LogLevel, Env
from skyflow.vault.data import InsertRequest, InsertRequestRecord

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

For **scoped / context-aware** tokens, add `roles` (list of role ids) and/or `context` to a
`path`/`credentials_string` credentials dict — they are embedded in the generated bearer token.

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

`vault_url` may be set on the vault config to override the URL derived from `cluster_id`/`env`.

## Timeouts and retries

HTTP timeout and retry behavior can be set at **two levels** — per-vault (keys on the vault config
dict) and client-wide (chainable builder methods) — resolved **per field: per-vault → client-wide →
SDK default**.

| Per-vault key | Builder method | Unit | Default | Meaning |
|---|---|---|---|---|
| `timeout` | `.timeout(s)` | seconds | `60` | Overall call ceiling (bounds the whole call incl. retries). |
| `connect_timeout` | `.connect_timeout(s)` | seconds | `10` | Per-attempt connection-establishment timeout. |
| `read_timeout` | `.read_timeout(s)` | seconds | `10` | Per-attempt response-read timeout. |
| `write_timeout` | `.write_timeout(s)` | seconds | `10` | Per-attempt request-write timeout. |
| `max_retries` | `.max_retries(n)` | int ≥ 0 | `0` | Retry attempts after the first failure. `0` = off. |
| `initial_retry_delay_millis` | `.initial_retry_delay_millis(ms)` | int ≥ 0 | `500` | Backoff before the first retry. |
| `max_retry_delay_millis` | `.max_retry_delay_millis(ms)` | int ≥ 0 | `2000` | Ceiling the exponential backoff grows to. |

```python
skyflow_client = (
    Skyflow.builder()
    .timeout(60).max_retries(3)                    # client-wide defaults
    .add_vault_config({
        'vault_id': '<VAULT_ID>', 'cluster_id': '<CLUSTER_ID>', 'env': Env.PROD,
        'credentials': {'api_key': '<API_KEY>'},
        'read_timeout': 30, 'max_retries': 2,      # per-vault overrides
    })
    .build()
)
```

Retries are **opt-in** (default `0`) so non-idempotent writes are never replayed silently. When
enabled, retryable responses (HTTP `408` / `429` / `5xx`) are retried with exponential backoff and
jitter. A large batch can exceed the default per-attempt timeouts, so raise `read_timeout`/`timeout`
for big bulk calls.

## Unary operations

A unary API error (the server rejects the call) raises a `SkyflowError` carrying the server's
`http_code`, `message`, `grpc_code`, `http_status`, and `details`. On success the response is a single
**`records`** list — one entry per input, each carrying its own `http_code` and `error`.

### Insert

`table_name`/`upsert` go at **exactly one** level — on the request (applies to all records) or on
every record — never both. `upsert` is an `UpsertOptions`; `tokens` is optional BYOT.

```python
from skyflow.vault.data import InsertRequest, InsertRequestRecord, UpsertOptions
from skyflow.utils.enums import UpsertType

request = InsertRequest(
    table_name='cards',
    upsert=UpsertOptions(unique_columns=['card_number'], update_type=UpsertType.UPDATE),
    records=[InsertRequestRecord(data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'})],
)
response = vault.insert(request)
for r in response.records:
    print(r['skyflow_id'], r['tokens'], r['http_code'], r['error'])
```
Each record: `{table_name, skyflow_id, tokens, hashed_data, http_code, error}` (no plaintext `data`).

### Get

Two mutually exclusive modes — single-table, or multi-table via `records=[GetRecordRequest(...)]`.
`column_redactions` entries are `ColumnRedaction` objects.

```python
from skyflow.vault.data import GetRequest, GetRecordRequest, ColumnRedaction

# single-table
vault.get(GetRequest(
    table_name='persons', ids=['<SKYFLOW_ID>'], columns=['name', 'email'],
    column_redactions=[ColumnRedaction(column_name='email', redaction='MASKED')],
))

# multi-table batch
vault.get(GetRequest(records=[
    GetRecordRequest(table_name='persons', ids=['<SKYFLOW_ID>'], columns=['name']),
    GetRecordRequest(table_name='cards', unique_values=[{'email': 'john@example.com'}]),
]))
```
Each record: `{table_name, skyflow_id, tokens, data, hashed_data, http_code, error}`.

### Update

```python
from skyflow.vault.data import UpdateRequest

vault.update(UpdateRequest(
    table_name='persons',
    records=[{'skyflow_id': '<SKYFLOW_ID>', 'data': {'name': 'Jane'}}],
))
```

### Delete

```python
from skyflow.vault.data import DeleteRequest

vault.delete(DeleteRequest(table_name='persons', ids=['<SKYFLOW_ID>']))
```
Each record: `{skyflow_id, http_code, error}`.

### Detokenize

`token_group_redactions` entries are `TokenGroupRedactions` objects.

```python
from skyflow.vault.data import DetokenizeRequest, TokenGroupRedactions

vault.detokenize(DetokenizeRequest(
    tokens=['<TOKEN>'],
    token_group_redactions=[TokenGroupRedactions(token_group_name='card_number_cg', redaction='MASKED')],
))
```
Each record: `{token, token_group_name, value, metadata, http_code, error}`.

### Query

```python
from skyflow.vault.data import QueryRequest

response = vault.query(QueryRequest(query="SELECT * FROM persons WHERE skyflow_id = '<SKYFLOW_ID>'"))
print(response.records)    # [{'data': {...}}, ...]
print(response.metadata)   # {'columns': [...]}
```

## Bulk operations

Bulk operations split the payload into batches sent **concurrently** and return a **`summary`** plus
a **`records`** list — one entry per submitted item, in input order, each tagged with its `index`.
A single bulk call accepts at most **10,000** items. Unlike unary calls, a bulk call does **not**
raise on a batch API error — every record's outcome is reported inline.

### Bulk insert

```python
from skyflow.vault.data import BulkInsertRequest, BulkInsertRequestRecord

request = BulkInsertRequest(table_name='cards', records=[
    BulkInsertRequestRecord(data={'card_number': '4111111111111111'}),
    BulkInsertRequestRecord(data={'card_number': '4222222222222222'}),
])

response = vault.bulk_insert(request)                 # synchronous
# response = await vault.bulk_insert_async(request)   # async variant

print(response.summary.total_records, response.summary.total_inserted, response.summary.total_failed)
for r in response.records:
    print(r['index'], r['skyflow_id'], r['http_code'], r['error'])

retry = response.records_to_retry()   # original records whose http_code is 500-599 (excl. 529)
```
`BulkInsertRequestRecord(data, table_name=None, tokens=None, upsert=None)` — mirrors Java's
`BulkInsertRequestRecord`; `tokens` is optional BYOT.

### Bulk detokenize

```python
from skyflow.vault.data import BulkDetokenizeRequest, TokenGroupRedactions

request = BulkDetokenizeRequest(
    tokens=['<TOKEN_1>', '<TOKEN_2>'],
    token_group_redactions=[TokenGroupRedactions(token_group_name='<TOKEN_GROUP_NAME>', redaction='MASKED')],
)

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

**Picking a concurrency value.** A good starting point is the standard formula
`N_concurrency = N_cpu × U_cpu × (1 + W/C)` — where `N_cpu` is the number of cores (`os.cpu_count()`),
`U_cpu` is your target CPU utilization (0–1, ≈1.0 if this is the only workload), and `W/C` is the
ratio of wait time (API latency) to compute time per task. Bulk work is I/O-bound, so `W/C` is large
and concurrency well above core count is usually optimal (up to the max of 10).

Merging is by input order regardless of which batch finishes first, so `index` always matches an
item's position in your submitted payload. A per-batch failure only fails that batch's records.

### Custom request headers

Bulk operations accept an optional `options` object whose **interceptor** runs **once per batch** and
can attach custom headers to that batch's request (mirrors Java's `RequestInterceptor`).

```python
from skyflow.vault.data import BulkInsertOptions, CustomHeaderKey

def add_request_id(context):
    # context.operation ('INSERT'/'DETOKENIZE'), context.batch_index, context.total_batches
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, f'req-{context.batch_index}')

vault.bulk_insert(request, BulkInsertOptions(interceptor=add_request_id))
```

- Options classes: `BulkInsertOptions(interceptor=...)`, `BulkDetokenizeOptions(interceptor=...)`.
- `CustomHeaderKey`: `SKYFLOW_ACCOUNT_ID` (`x-skyflow-account-id`), `SKYFLOW_ACCOUNT_NAME`
  (`x-skyflow-account-name`), `REQUEST_ID_HEADER` (`x-request-id`).
- The interceptor runs once per batch, so a value it generates (e.g. a fresh request id) differs
  between batches; its headers are merged on top of the SDK's own (metrics + `Authorization`).

## Error handling

- **Validation errors** (invalid request, missing credentials, over the 10,000 ceiling) — raised as a
  `SkyflowError` before any network call, for every operation.
- **Unary API errors** (the server rejects the call: 4xx/5xx) — raised as a `SkyflowError` with the
  server's `http_code`, `message`, `grpc_code`, `http_status`, and `details`.
- **Bulk / per-record failures** — the bulk call itself does not raise; each entry in `records`
  reports its own `http_code` and `error`, and `records_to_retry()` / `tokens_to_retry()` return the
  inputs worth resending (retryable `5xx`).

```python
from skyflow.error import SkyflowError

# unary — an API error raises
try:
    response = vault.insert(request)
except SkyflowError as e:
    print(e.http_code, e.message, e.grpc_code, e.details)

# bulk — inspect per-record outcomes, nothing raised for API errors
response = vault.bulk_insert(bulk_request)
for r in response.records:
    if r['error'] is not None:
        print('row', r['index'], 'failed', r['http_code'], r['error'])
```

## Logging

The SDK logs at `LogLevel.ERROR` by default. Change it with
`Skyflow.builder().set_log_level(LogLevel.INFO)` (`DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`). The
batching warnings above are emitted at `WARN`.

## Samples

Runnable examples live in [samples/](samples/) — one file per operation, with sync/async pairs for
the bulk ops, plus custom-header, timeout/retry, and service-account examples. See
[samples/README.md](samples/README.md) to run them.
