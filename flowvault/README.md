# Skyflow FlowVault Python SDK

The `flowvault` module is a Skyflow Python SDK built for high-throughput vault operations. It shares its client, credentials, and configuration with the [skyvault SDK](../skyvault/README.md) (both depend on the `common` module) but exposes a different, narrower surface: **unary** vault operations plus **bulk** (batched, concurrent) insert and detokenize.

> Meant for **Flow DB** vaults.

> **`skyflow-flowvault-python` is versioned independently of the main `skyflow` SDK.** The two are separate PyPI artifacts with separate version lines, so a lower `flowvault` version number does not mean it is older or behind. Upgrade each artifact on its own; the current release is listed on [PyPI](https://pypi.org/project/skyflow-flowvault-python/).

[![CI](https://img.shields.io/static/v1?label=CI&message=passing&color=green?style=plastic&logo=github)](https://github.com/skyflowapi/skyflow-python/actions)
[![License](https://img.shields.io/github/license/skyflowapi/skyflow-python)](https://github.com/skyflowapi/skyflow-python/blob/main/LICENSE)

# Table of Contents

- [Table of Contents](#table-of-contents)
- [Overview](#overview)
- [Install](#install)
  - [Requirements](#requirements)
  - [Configuration](#configuration)
- [Quickstart](#quickstart)
- [Authenticate](#authenticate)
  - [Credential types](#credential-types)
  - [Where credentials can be set](#where-credentials-can-be-set)
  - [Generate a bearer token](#generate-a-bearer-token)
  - [Generate bearer tokens with context](#generate-bearer-tokens-with-context)
  - [Generate scoped bearer tokens](#generate-scoped-bearer-tokens)
  - [Generate signed data tokens](#generate-signed-data-tokens)
- [Initialize the client](#initialize-the-client)
  - [VaultConfig reference](#vaultconfig-reference)
  - [Skyflow.builder() reference](#skyflowbuilder-reference)
  - [Timeouts and retries](#timeouts-and-retries)
  - [Logging](#logging)
  - [Concurrency, thread safety, and resource lifecycle](#concurrency-thread-safety-and-resource-lifecycle)
- [VaultController — Bulk operations](#vaultcontroller--bulk-operations)
  - [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults)
  - [Batching and concurrency](#batching-and-concurrency)
- [VaultController — Unary operations](#vaultcontroller--unary-operations)
  - [Unary vs. bulk parity](#unary-vs-bulk-parity)
  - [Vault type support](#vault-type-support)
- [SDK Guidelines: Unary vs Bulk Operations](#sdk-guidelines-unary-vs-bulk-operations)
  - [Unary](#unary)
  - [Bulk](#bulk)
  - [Concurrency guidelines](#concurrency-guidelines)
- [Bulk Insert](#bulk-insert)
- [Bulk Detokenize](#bulk-detokenize)
- [Insert](#insert)
- [Detokenize](#detokenize)
- [Get](#get)
- [Update](#update)
- [Delete](#delete)
- [Custom Request Headers](#custom-request-headers)
- [Error Handling](#error-handling)
  - [Two layers of errors](#two-layers-of-errors)
  - [Per-record success and failure](#per-record-success-and-failure)
  - [Catching SkyflowError](#catching-skyflowerror)
  - [SkyflowError properties](#skyflowerror-properties)
  - [Retrying the failed records](#retrying-the-failed-records)
- [Samples](#samples)

# Overview

- Authenticate using a Skyflow service account, an API key, or a bearer token — see [Authenticate](#authenticate).
- Perform bulk Vault API operations — insert and detokenize — each with a synchronous and an async variant, built for high-throughput Flow DB workloads.
- Perform unary Vault API operations — insert, get, update, delete, and detokenize — a single API call each, for when you want a plain request and response rather than the bulk batching machinery. See [VaultController — Unary operations](#vaultcontroller--unary-operations).
- **Per-record reporting, not all-or-nothing.** A bulk call succeeds as a call even when individual records fail; every response reports a summary plus the outcome of each individual record or token. See [Error Handling](#error-handling).

# Install

## Requirements

- Python 3.9 and above

## Configuration

```bash
pip install skyflow-flowvault-python
```

The package installs under the import name `skyflow`:

```python
from skyflow import Skyflow, LogLevel, Env
```

Check [PyPI](https://pypi.org/project/skyflow-flowvault-python/) for the current version and [GitHub releases](https://github.com/skyflowapi/skyflow-python/releases) for what changed in each one.

# Quickstart

```python
from skyflow import Skyflow, LogLevel, Env
from skyflow.vault.data import InsertRequest, InsertRequestRecord

credentials = {'api_key': '<API_KEY>'}  # or 'token' / 'path' / 'credentials_string'

vault_config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',   # part of the vault URL: https://{cluster_id}.vault.skyflowapis.com
    'env': Env.PROD,                # DEV, STAGE, SANDBOX, or PROD (default)
    'credentials': credentials,
}

skyflow_client = (
    Skyflow.builder()
    .add_vault_config(vault_config)
    .build()
)

# Returns the controller for the given vault
vault = skyflow_client.vault('<VAULT_ID>')

response = vault.insert(InsertRequest(
    table_name='cards',
    records=[InsertRequestRecord(data={'card_number': '4111111111111111'})],
))
print(response.records)
```

`vault('<VAULT_ID>')` returns the controller for a specific registered vault. `vault()` with no argument returns the controller for the first vault added to the builder. To talk to more than one vault from a single client, register each with `add_vault_config(...)` and fetch each controller by ID.

# Authenticate

Requests are authorized with Skyflow credentials that you attach to the vault config's `credentials` dict. Credential handling comes from the shared `common` module, so it works the same way `skyvault` does.

## Credential types

Set **exactly one** of the following keys on the `credentials` dict. If you set more than one, the resolution is undefined — pick one.

| Key | What it is |
|---|---|
| `api_key` | A long-lived key that authenticates and authorizes requests to the API. Simplest option. |
| `token` | A short-lived bearer token, typically generated from service account credentials. See [Generate a bearer token](#generate-a-bearer-token). |
| `path` | Filesystem path to a service account `credentials.json`. The SDK generates and refreshes bearer tokens from it. |
| `credentials_string` | The contents of a service account `credentials.json` as a JSON string — use this when the credentials come from a secret store rather than a file. |

Two optional modifiers apply when the SDK is generating tokens for you (that is, with `path` or `credentials_string`):

| Key | Description |
|---|---|
| `roles` | Restrict the generated token to specific role IDs (a scoped token). |
| `context` | Attach context to the generated token for context-aware authorization. |

```python
# API key
credentials = {'api_key': '<API_KEY>'}

# Bearer token you generated yourself
credentials = {'token': '<BEARER_TOKEN>'}

# Service account credentials file — the SDK handles token generation and refresh
credentials = {'path': '<PATH_TO_CREDENTIALS_JSON>'}

# Service account credentials as a JSON string
credentials = {'credentials_string': '<CREDENTIALS_JSON_STRING>'}
```

## Where credentials can be set

Credentials resolve **most specific first**:

1. **Per-vault** — `vault_config['credentials']`. Wins for that vault.
2. **Client-wide** — `Skyflow.builder().add_skyflow_credentials(credentials)`. Used by any vault that has none of its own.
3. **Environment** — if neither is provided, the SDK reads the `SKYFLOW_CREDENTIALS` environment variable.

If none of the three yields credentials, the call fails with a `SkyflowError`.

## Generate a bearer token

If you would rather manage tokens yourself, the service-account utilities ship inside `skyflow-flowvault-python` under `skyflow.service_account`. They are plain functions:

- `generate_bearer_token(path, options=None)` — mint a token from a service account credentials **file path**.
- `generate_bearer_token_from_creds(credentials_string, options=None)` — the same, from the credentials JSON as a **string**.
- `is_expired(token)` — `True` when the token is empty or past expiry; use it to reuse a cached token until it expires.
- `generate_signed_data_tokens(path, options)` / `generate_signed_data_tokens_from_creds(credentials_string, options)` — see [Generate signed data tokens](#generate-signed-data-tokens).

Each `generate_bearer_token*` call returns a `(token, ...)` tuple — unpack the first element. Tokens are valid for 60 minutes and carry the service account's permissions.

[Example](https://github.com/skyflowapi/skyflow-python/blob/main/flowvault/samples/service_account/bearer_token_generation_example.py):

```python
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired

bearer_token = ''

def get_token(file_path):
    global bearer_token
    if not is_expired(bearer_token):
        return bearer_token          # reuse until it expires
    token, _ = generate_bearer_token(file_path)
    bearer_token = token
    return bearer_token

# ...or from a credentials JSON string
token, _ = generate_bearer_token_from_creds(credentials_string)
```

To use the token with the SDK, put it on the `credentials` dict:

```python
credentials = {'token': token}
```

## Generate bearer tokens with context

**Context-aware authorization** embeds context values into a bearer token during generation so your policies can reference them. This enables more flexible access controls, such as tracking end-user identity when calling through a service account, and is required for detokenizing signed data tokens.

Pass an `options` dict with a `ctx` key — either a **string** or a **dict**:

```python
# String context — a single value your policy references as request.context
token, _ = generate_bearer_token(file_path, {'ctx': 'user_12345'})

# Dict context — each key maps to a Skyflow CEL policy variable under request.context.*
token, _ = generate_bearer_token(file_path, {'ctx': {
    'role': 'admin',
    'department': 'finance',
    'user_id': 'user_12345',
}})
```

With the dict above, your Skyflow policies can reference `request.context.role`, `request.context.department`, and `request.context.user_id` to make conditional access decisions.

[Full example](https://github.com/skyflowapi/skyflow-python/blob/main/flowvault/samples/service_account/bearer_token_generation_with_context_example.py)

## Generate scoped bearer tokens

A service account with multiple roles can generate bearer tokens limited to specific roles by passing their role IDs in `options['role_ids']`. This is useful for services with several responsibilities, such as separating billing access from analytics access. The generated tokens are valid for 60 minutes and can only execute operations permitted by the designated roles.

[Example](https://github.com/skyflowapi/skyflow-python/blob/main/flowvault/samples/service_account/scoped_token_generation_example.py):

```python
from skyflow.service_account import generate_bearer_token

options = {'role_ids': ['<YOUR_ROLE_ID1>', '<YOUR_ROLE_ID2>']}
token, _ = generate_bearer_token(file_path, options)
# ...or from a credentials string: generate_bearer_token_from_creds(credentials_string, options)
```

To generate bearer tokens concurrently from several threads, see [bearer_token_generation_using_threads_example.py](https://github.com/skyflowapi/skyflow-python/blob/main/flowvault/samples/service_account/bearer_token_generation_using_threads_example.py).

## Generate signed data tokens

Skyflow generates data tokens when sensitive data is inserted into the vault. Those data tokens can be digitally signed with the private key of the service account credentials, which adds a further layer of protection. A signed token can only be detokenized by passing it together with a bearer token generated from service account credentials that hold the matching context and permissions.

`options` accepts `ctx` (string or dict, same format as bearer tokens), `data_tokens` (the tokens to sign), and `time_to_live` (seconds):

```python
from skyflow.service_account import generate_signed_data_tokens, generate_signed_data_tokens_from_creds

options = {
    'ctx': 'user_12345',
    'data_tokens': ['<DATA_TOKEN1>', '<DATA_TOKEN2>'],
    'time_to_live': 30,  # seconds
}
results = generate_signed_data_tokens(file_path, options)
# ...or from a credentials string: generate_signed_data_tokens_from_creds(credentials_string, options)

for data_token, signed_data_token in results:
    print(data_token, '->', signed_data_token)
```

`generate_signed_data_tokens*` returns a list of `(data_token, signed_data_token)` tuples.

[Full example](https://github.com/skyflowapi/skyflow-python/blob/main/flowvault/samples/service_account/signed_token_generation_example.py)

# Initialize the client

`Skyflow` is the client. Build it once, keep it for the lifetime of your application, and get a `VaultController` from it with `vault(...)`.

```python
from skyflow import Skyflow, LogLevel, Env

# Step 1: Credentials — exactly one credential type
credentials = {'path': '<PATH_TO_CREDENTIALS_JSON>'}

# Step 2: Vault configuration
vault_config = {
    'vault_id': '<VAULT_ID>',
    'cluster_id': '<CLUSTER_ID>',
    'env': Env.PROD,            # DEV, STAGE, SANDBOX, or PROD (default)
    'credentials': credentials,
    # Optional: vault-level HTTP overrides
    'timeout': 120,             # overall call timeout, in seconds
    'max_retries': 2,           # retries after the first failure
}

# Step 3: Build the client
skyflow_client = (
    Skyflow.builder()
    .set_log_level(LogLevel.INFO)   # default is ERROR
    .add_vault_config(vault_config)
    .build()
)

# Step 4: Get the controller and issue calls
vault = skyflow_client.vault('<VAULT_ID>')
```

## VaultConfig reference

The vault config is a plain dict:

| Key | Required | Description |
|---|---|---|
| `vault_id` | required | The vault's ID. |
| `cluster_id` | required | The cluster portion of the vault URL — `https://{cluster_id}.vault.skyflowapis.com`. |
| `env` | optional | `Env.DEV`, `Env.STAGE`, `Env.SANDBOX`, or `Env.PROD`. Defaults to `PROD`. |
| `credentials` | optional | Credentials for this vault. Falls back to client-wide credentials, then `SKYFLOW_CREDENTIALS`. |
| `vault_url` | optional | Full vault URL, when it cannot be derived from `cluster_id` and `env`. |
| `timeout` | optional | Overall call timeout in seconds, including retries. |
| `connect_timeout` | optional | Per-attempt connection timeout, in seconds. |
| `read_timeout` | optional | Per-attempt response-read timeout, in seconds. |
| `write_timeout` | optional | Per-attempt request-write timeout, in seconds. |
| `max_retries` | optional | Retry attempts after the first failure. |
| `initial_retry_delay_millis` | optional | Backoff before the first retry, in milliseconds. |
| `max_retry_delay_millis` | optional | Ceiling the exponential backoff grows to, in milliseconds. |

## Skyflow.builder() reference

| Method | Description |
|---|---|
| `add_vault_config(config)` | Register a vault. The first one registered is what `vault()` (no argument) returns. |
| `update_vault_config(config)` | Update a registered vault in place. |
| `remove_vault_config(vault_id)` | Unregister a vault. |
| `add_skyflow_credentials(credentials)` | Client-wide credentials for vaults that don't set their own. |
| `set_log_level(log_level)` | `LogLevel.DEBUG`, `INFO`, `WARN`, `ERROR` (default), or `OFF`. |
| `timeout(s)` / `connect_timeout(s)` / `read_timeout(s)` / `write_timeout(s)` | Client-wide HTTP timeouts, in seconds. |
| `max_retries(n)` / `initial_retry_delay_millis(ms)` / `max_retry_delay_millis(ms)` | Client-wide retry policy. |
| `build()` | Produce the `Skyflow` client. |

Once built, `skyflow_client.vault('<VAULT_ID>')` returns the controller for a specific registered vault, which is how one client talks to more than one vault.

## Timeouts and retries

Each HTTP setting resolves **most specific first**: the value on the vault config, else the client-wide value on `Skyflow.builder()`, else the SDK default.

| Setting | SDK default |
|---|---|
| `timeout` (overall call, incl. retries) | 60 s |
| `connect_timeout` / `read_timeout` / `write_timeout` (per attempt) | 10 s |
| `max_retries` | `0` — retries are **opt-in**, so non-idempotent writes are never replayed silently |
| `initial_retry_delay_millis` | 500 ms |
| `max_retry_delay_millis` | 2000 ms |

```python
skyflow_client = (
    Skyflow.builder()
    .timeout(60).max_retries(3)                    # client-wide policy
    .initial_retry_delay_millis(500).max_retry_delay_millis(4000)
    .add_vault_config({
        'vault_id': '<VAULT_ID>', 'cluster_id': '<CLUSTER_ID>', 'env': Env.PROD,
        'credentials': {'api_key': '<API_KEY>'},
        'timeout': 300, 'read_timeout': 30,        # per-vault overrides
    })
    .build()
)
```

When retries are enabled, retryable responses (HTTP `408` / `429` / `5xx`) are retried with exponential backoff and jitter, bounded by the `initial`/`max` delays and the overall `timeout`. A large bulk batch can exceed the default per-attempt timeouts, so raise `read_timeout`/`timeout` for big bulk calls.

## Logging

The SDK logs at `LogLevel.ERROR` by default. Levels rank `DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`; setting a level prints that level and everything above it. Change it with `Skyflow.builder().set_log_level(LogLevel.DEBUG)`.

## Concurrency, thread safety, and resource lifecycle

- **Thread safety** — `Skyflow` and every `VaultController` it hands out are meant to be built once and reused for the application's lifetime; the underlying HTTP client is reused across calls rather than recreated per request.
- **Async execution** — each `*_async` bulk call runs its batches under an `asyncio.Semaphore` sized to that call's concurrency limit (see [Batching and concurrency](#batching-and-concurrency)). The synchronous bulk calls run their batches on a `ThreadPoolExecutor` sized the same way, scoped to the call.

# VaultController — Bulk operations

`VaultController` is returned by `skyflow_client.vault(...)`. `flowvault` exposes these bulk vault operations:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `bulk_insert(request)` | `BulkInsertRequest`, optional `BulkInsertOptions` | `BulkInsertResponse` | Insert many records, optionally across multiple tables, in one call |
| `bulk_insert_async(request)` | same | `BulkInsertResponse` (awaitable) | Async variant of `bulk_insert` |
| `bulk_detokenize(request)` | `BulkDetokenizeRequest`, optional `BulkDetokenizeOptions` | `BulkDetokenizeResponse` | Detokenize many tokens, optionally with a redaction override per token group |
| `bulk_detokenize_async(request)` | same | `BulkDetokenizeResponse` (awaitable) | Async variant of `bulk_detokenize` |

## Schema vs. schemaless vaults

Which operations make sense depends on whether the vault is **structured** (has a schema — tables and columns) or **schemaless** (stores standalone tokens with no table structure):

| Operation | Supported on |
|---|---|
| `bulk_insert` / `bulk_insert_async` | Structured (schema) vaults — inserts into a table's columns. |
| `bulk_detokenize` / `bulk_detokenize_async` | Both — detokenizing only needs the token itself, not a table, so it works regardless of which kind of vault the token came from. |

Each method also accepts an optional options object (`BulkInsertOptions`, `BulkDetokenizeOptions`) — see [Custom Request Headers](#custom-request-headers).

A single bulk call accepts at most **10,000** records or tokens; anything larger is rejected up front with a `SkyflowError`. Under that ceiling the SDK splits the payload into batches and sends them concurrently, which is why errors from one call can carry different `request_id` values.

Every bulk response has the same two-part shape:

- a **summary** — totals for the call (e.g. `total_records` / `total_inserted` / `total_failed` for insert)
- a **records** list — one entry per submitted record or token, in input order, each carrying its own `index`, `http_code`, and `error`

That per-record shape is the point of these APIs; see [Error Handling](#error-handling) for the full model.

## Batching and concurrency

Batch size and concurrency are configured **per operation** through environment variables — there is no builder or options API for them. Each value is read from the process environment first, then from a `.env` file in the working directory (via `python-dotenv`).

| Operation | Batch size variable | Default | Max | Concurrency variable | Default | Max |
|-----------|--------------------|---------|-----|---------------------|---------|-----|
| Bulk insert | `INSERT_BATCH_SIZE` | 50 | 1000 | `INSERT_CONCURRENCY_LIMIT` | 1 | 100 |
| Bulk detokenize | `DETOKENIZE_BATCH_SIZE` | 50 | 1000 | `DETOKENIZE_CONCURRENCY_LIMIT` | 1 | 100 |

Concurrency defaults to **1**, so batches are sent one after another unless you raise the limit.

How each value is resolved:

- **Batch size** — `min(your_value, max)`. Above the max, the SDK logs a warning and uses the max. Zero, negative, or non-numeric values log a warning and fall back to the default.
- **Concurrency** — `min(your_value, max, batch_count)`, where `batch_count = ceil(item_count / batch_size)`. Concurrency never exceeds the number of batches there are to run. Same warning-and-fallback behaviour for invalid values.

Those warnings are emitted at `WARN`, which the default `ERROR` level hides — set `LogLevel.WARN` or below to see them (see [Logging](#logging)).

For example, 500 records with `INSERT_BATCH_SIZE=100` and `INSERT_CONCURRENCY_LIMIT=10` produces 5 batches, all 5 in flight at once — the concurrency is capped to 5, not 10.

```dotenv
# .env
INSERT_BATCH_SIZE=100
INSERT_CONCURRENCY_LIMIT=5
```

The 10,000-item ceiling per bulk call is a separate, fixed limit and is not configurable.

# VaultController — Unary operations

Alongside the bulk methods, `VaultController` exposes five **unary** operations. Each sends exactly one API call and hands the result straight back:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `insert(request)` | `InsertRequest`, optional `InsertOptions` | `InsertResponse` | Insert records, optionally across multiple tables, in one call |
| `detokenize(request)` | `DetokenizeRequest`, optional `DetokenizeOptions` | `DetokenizeResponse` | Detokenize tokens, optionally with a redaction override per token group |
| `get(request)` | `GetRequest`, optional `GetOptions` | `GetResponse` | Read records by skyflow ID or unique value, optionally with a redaction override per column |
| `update(request)` | `UpdateRequest`, optional `UpdateOptions` | `UpdateResponse` | Update records by skyflow ID |
| `delete(request)` | `DeleteRequest`, optional `DeleteOptions` | `DeleteResponse` | Delete records by skyflow ID or unique value |

`insert` and `detokenize` are the unary counterparts of `bulk_insert` and `bulk_detokenize` — the same request builders, sent as one call instead of many batches. `get`, `update`, and `delete` have no bulk counterpart at all; they exist only in this unary form.

Each method also accepts an optional options object (`InsertOptions`, `DetokenizeOptions`, `GetOptions`, `UpdateOptions`, `DeleteOptions`) — see [Custom Request Headers](#custom-request-headers).

## Unary vs. bulk parity

Everything the bulk machinery adds — batching, concurrency, the summary, the per-item index — is absent here. What survives is the per-record reporting:

| | Bulk operations | Unary operations |
|---|---|---|
| Async variant | Yes — `bulk_insert_async`, `bulk_detokenize_async` | **No.** Wrap the call yourself if you need one |
| Batching and concurrency | Configured per operation — see [Batching and concurrency](#batching-and-concurrency) | Not applicable — one payload, one call |
| Payload ceiling | 10,000 records or tokens per call | 10,000 for `insert`; otherwise the vault's own request limits apply |
| Response summary | `response.summary` | None — read the records list |
| Per-item `index` | Yes | No. Records come back in submitted order |
| Retry helper | `records_to_retry()` / `tokens_to_retry()` | None — filter the records yourself, see [Retrying the failed records](#retrying-the-failed-records) |
| Per-item `http_code` / `error` / `request_id` | Yes | Yes, on every unary operation |

## Vault type support

The same distinction as [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults) applies. Four of the five unary operations address records inside a table, so they only make sense against a structured vault:

| Operation | Supported on |
|---|---|
| `insert` | Structured (schema) vaults — inserts into a table's columns. |
| `get` | Structured vaults — reads a table's records by skyflow ID or unique value. |
| `update` | Structured vaults — updates a table's records by skyflow ID. |
| `delete` | Structured vaults — deletes a table's records. |
| `detokenize` | Both — detokenizing only needs the token itself, not a table, so it works regardless of which kind of vault the token came from. |

# SDK Guidelines: Unary vs Bulk Operations

Both **Unary** and **Bulk** operations accept as many records as you pass. The key difference is **how the SDK makes HTTP calls and manages concurrency**.

## Unary

- Makes **exactly one HTTP call per SDK invocation**, regardless of the number of records.
- The application is responsible for any **chunking, batching, and concurrency**.
- Best suited for:
  - Single-event or low-volume ingestion
  - Interactive or user-facing requests where immediate results are required
  - Applications that already have their own concurrency or job-management mechanism

**Use Unary when you want the application to control request execution.**

## Bulk

- The SDK automatically splits records into `batch_size`-sized chunks.
- It dispatches up to `concurrency_limit` batches in parallel.
- The SDK therefore owns **batching, parallel dispatch, and request coordination**.
- Best suited for:
  - Large datasets
  - Imports and backfills
  - ETL and data migration workloads
  - Bulk/streaming ingestion where you want the SDK to manage batching and concurrency

**Use Bulk when you want the SDK to optimize request execution for high-volume workloads.**

A bulk call sent with fewer records than `batch_size` (default 50) still produces exactly one batch — `concurrency` resolves to 1 regardless of `..._CONCURRENCY_LIMIT` — so there's no batching benefit, only the overhead of the bulk machinery on top. Use unary instead for calls at that size.

## Concurrency guidelines

For Bulk operations, choose `concurrency_limit` based on the available CPU and the ratio of task wait time to compute time:

```
concurrency ≈ N_cpu × U_cpu × (1 + W/C)
```

Where:

- `N_cpu` = number of CPU cores available to the process (`os.cpu_count()`)
- `U_cpu` = target CPU utilization, between 0 and 1
- `W` = wait time / API latency per call
- `C` = compute time per call — approximately **5 ms for the SDK**

### Practical guidance

- **VUs ≤ 20:** a single CPU core is generally sufficient.
- **VUs > 20:** consider increasing CPU capacity and tune concurrency accordingly.
- For higher-throughput workloads, **dual- or quad-core** configurations are a good starting point.
- Start with the formula as a baseline and **benchmark with your actual API latency and workload** before increasing concurrency further.

# Bulk Insert

Insert many records — even across different tables — in a single call. Each record is a `BulkInsertRequestRecord` with its own `data` and, optionally, its own `table_name` and `upsert`.

> **Vault type supported:** structured (schema) vaults. See [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults).

**Note:**

- `table_name` must be specified at exactly one level: either on the request (`BulkInsertRequest(table_name=...)`) or on **every** record (`BulkInsertRequestRecord(table_name=...)`) — not both, and not neither.
- `upsert` is optional, but wherever you supply it, it must sit at the same level as `table_name`.
- `UpsertOptions` requires `unique_columns`. `update_type` accepts `UpsertType.UPDATE` or `UpsertType.REPLACE` — if omitted, the SDK sends no `update_type` at all, and the vault treats that the same as an update.
- `tokens` is optional bring-your-own-token.

```python
from skyflow.vault.data import BulkInsertRequest, BulkInsertRequestRecord, UpsertOptions
from skyflow.utils.enums import UpsertType

request = BulkInsertRequest(records=[
    # table_name lives on each record here
    BulkInsertRequestRecord(table_name='table1', data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'}),
    BulkInsertRequestRecord(
        table_name='table2',
        data={'email': 'jane.doe@example.com'},
        upsert=UpsertOptions(unique_columns=['email'], update_type=UpsertType.UPDATE),
    ),
])

response = vault.bulk_insert(request)               # synchronous
# response = await vault.bulk_insert_async(request) # async variant
print(response.summary.total_inserted, 'of', response.summary.total_records)
```

To put the table name on the request instead, drop `table_name` from every record and set it once:

```python
request = BulkInsertRequest(
    table_name='table1',
    upsert=UpsertOptions(unique_columns=['email'], update_type=UpsertType.UPDATE),
    records=[BulkInsertRequestRecord(data={'card_number': '4111111111111111'})],
)
```

Sample response:

```json
{
  "summary": { "total_records": 2, "total_inserted": 1, "total_failed": 1 },
  "records": [
    {
      "index": 0,
      "request_id": null,
      "table_name": "table1",
      "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1",
      "tokens": {
        "card_number": [ { "token": "5484-7829-1702-9110", "token_group_name": "card_number_cg", "path": null } ]
      },
      "hashed_data": { "card_number": [ { "data": "b6e6d...c3f9", "hash_name": "hash1" } ] },
      "http_code": 200,
      "error": null
    },
    {
      "index": 1,
      "request_id": "a1b2c3d4-...",
      "table_name": "table2",
      "skyflow_id": null,
      "tokens": null,
      "hashed_data": null,
      "http_code": 400,
      "error": "Insert failed. Column email is invalid."
    }
  ]
}
```

`.tokens` maps each column to a **list** of `Token` objects — one entry per token group configured on that column, so a column with a single token group still comes back as a one-element list, not a bare string. Each `Token` has `.token`, `.token_group_name`, and `.path` (the location within a structured column's value the token came from, e.g. `"phone_numbers[0].type"`; `None` for a flat column). `.tokens` is `None` when the record has no tokens (e.g. a failed record). Insert records omit plaintext `.data`.

```python
for record in response.records:
    if record.error is None:
        print(record.index, record.table_name, '->', record.skyflow_id)
    else:
        print(record.index, 'failed', record.http_code, record.error)
```

Accessors on each `BulkInsertResponseRecord`: `.index`, `.table_name`, `.skyflow_id`, `.tokens`, `.hashed_data`, `.http_code`, `.error`, `.request_id`.

Use `response.records_to_retry()` to get back only the `BulkInsertRequestRecord`s worth resubmitting — see [Retrying the failed records](#retrying-the-failed-records).

# Bulk Detokenize

Detokenize many tokens in one call, optionally overriding the redaction applied per token group via `token_group_redactions`.

> **Vault type supported:** both. See [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults).

```python
from skyflow.vault.data import BulkDetokenizeRequest, TokenGroupRedactions

request = BulkDetokenizeRequest(
    tokens=['5479-4229-4622-1393', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'],
    token_group_redactions=[TokenGroupRedactions(token_group_name='card_number_cg', redaction='MASKED')],
)

response = vault.bulk_detokenize(request)               # synchronous
# response = await vault.bulk_detokenize_async(request) # async variant
```

Sample response:

```json
{
  "summary": { "total_tokens": 2, "total_detokenized": 1, "total_failed": 1 },
  "records": [
    {
      "index": 0,
      "request_id": null,
      "token": "5479-4229-4622-1393",
      "value": "4111111111111111",
      "token_group_name": "card_number_cg",
      "metadata": { "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1", "table_name": "table1" },
      "http_code": 200,
      "error": null
    },
    {
      "index": 1,
      "request_id": "a1b2c3d4-...",
      "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "value": null,
      "token_group_name": null,
      "metadata": null,
      "http_code": 404,
      "error": "Token Not Found"
    }
  ]
}
```

`record.metadata` is a typed `DetokenizeResponseRecordMetadata` with `.skyflow_id` / `.table_name` (`None` on records that errored):

```python
for record in response.records:
    if record.error is None:
        print(record.token, '->', record.value, '(', record.token_group_name, ')')
    else:
        print(record.token, 'failed', record.http_code, record.error)
```

Accessors on each `BulkDetokenizeResponseRecord`: `.index`, `.token`, `.value`, `.token_group_name`, `.metadata`, `.http_code`, `.error`, `.request_id`.

Use `response.tokens_to_retry()` to get back only the tokens worth resubmitting.

# Insert

Insert records in a single API call — the unary counterpart of [Bulk Insert](#bulk-insert), with no batching or concurrency involved. Each record is an `InsertRequestRecord` with its own `data` and, optionally, its own `table_name`, `tokens`, and `upsert`.

> **Vault type supported:** structured (schema) vaults. See [Vault type support](#vault-type-support).

**Note:**

- `table_name`/`upsert` follow the same one-level rule as [Bulk Insert](#bulk-insert): on the request (applies to all records) or on every record — never both.
- `tokens` is optional bring-your-own-token; when supplied, the map must not be empty and no key or value may be blank.

```python
from skyflow.vault.data import InsertRequest, InsertRequestRecord, UpsertOptions
from skyflow.utils.enums import UpsertType

request = InsertRequest(
    table_name='cards',
    upsert=UpsertOptions(unique_columns=['card_number'], update_type=UpsertType.UPDATE),
    records=[InsertRequestRecord(data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'})],
)
response = vault.insert(request)
```

There is no async variant: `insert` returns its `InsertResponse` directly.

Sample response:

```json
{
  "records": [
    {
      "table_name": "cards",
      "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1",
      "tokens": {
        "card_number": [ { "token": "5484-7829-1702-9110", "token_group_name": "card_number_cg", "path": null } ]
      },
      "hashed_data": { "card_number": [ { "data": "b6e6d...c3f9", "hash_name": "hash1" } ] },
      "http_code": 200,
      "error": null,
      "request_id": null
    }
  ]
}
```

There is no `summary` and no per-record `index` — the records come back in the order you submitted them. `request_id` behaves exactly as on a bulk record: `None` on success, the failing call's `x-request-id` on error. `.tokens` is the same parsed dict-of-`Token`-lists described under [Bulk Insert](#bulk-insert). Insert records omit plaintext `.data`.

```python
for record in response.records:
    if record.error is None:
        print(record.skyflow_id, record.tokens)
    else:
        print('insert failed', record.http_code, record.error)
```

Accessors on each `InsertResponseRecord`: `.table_name`, `.skyflow_id`, `.tokens`, `.hashed_data`, `.http_code`, `.error`, `.request_id`.

# Detokenize

Detokenize tokens in a single API call — the unary counterpart of [Bulk Detokenize](#bulk-detokenize), optionally overriding the redaction applied per token group via `token_group_redactions`.

> **Vault type supported:** both. See [Vault type support](#vault-type-support).

**Note:**

- `tokens` is required and must not be empty, and no entry may be blank.
- `token_group_redactions` is optional; when supplied, each entry needs a non-blank `token_group_name` and `redaction`. Entries are `TokenGroupRedactions` objects.

```python
from skyflow.vault.data import DetokenizeRequest, TokenGroupRedactions

request = DetokenizeRequest(
    tokens=['5479-4229-4622-1393', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'],
    token_group_redactions=[TokenGroupRedactions(token_group_name='card_number_cg', redaction='MASKED')],
)
response = vault.detokenize(request)
```

There is no async variant: `detokenize` returns its `DetokenizeResponse` directly.

Sample response:

```json
{
  "records": [
    {
      "token": "5479-4229-4622-1393",
      "value": "4111111111111111",
      "token_group_name": "card_number_cg",
      "metadata": { "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1", "table_name": "table1" },
      "http_code": 200,
      "error": null,
      "request_id": null
    },
    {
      "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "value": null,
      "token_group_name": null,
      "metadata": null,
      "http_code": 404,
      "error": "Token Not Found",
      "request_id": "a1b2c3d4-..."
    }
  ]
}
```

Same per-record shape as bulk detokenize, minus `index`. `record.metadata` is a typed `DetokenizeResponseRecordMetadata` with `.skyflow_id` / `.table_name` (`None` on records that errored).

```python
for record in response.records:
    if record.error is None:
        print(record.token, '->', record.value, '(', record.token_group_name, ')')
    else:
        print(record.token, 'failed', record.http_code, record.error)
```

Accessors on each `DetokenizeResponseRecord`: `.token`, `.value`, `.token_group_name`, `.metadata`, `.http_code`, `.error`, `.request_id`.

# Get

Read records back from a table, by skyflow ID or by unique value, optionally overriding the redaction applied per column via `column_redactions`.

> **Vault type supported:** structured (schema) vaults. See [Vault type support](#vault-type-support).

**Note:**

- A `GetRequest` works in one of two modes, and they are mutually exclusive: **single-table** (`table_name`, `skyflow_ids`/`unique_values`, `columns`, `column_redactions`, `limit`, `offset`) or **multi-table** (`records`, a list of `GetRequestRecord`). Setting fields from both modes fails validation.
- `table_name` is required, and exactly one of `skyflow_ids` or `unique_values` must be supplied — both, or neither, fails validation. This holds per record in multi-table mode.
- `unique_values` is a list of dicts: one dict per record, each holding the unique column-name/value pairs that identify it.
- `columns` selects the columns to return; omit it for all of them.
- `limit` and `offset` apply to the call as a whole and are **only used in single-table mode**.
- `column_redactions` entries are `ColumnRedactions` objects.

```python
from skyflow.vault.data import GetRequest, GetRequestRecord, ColumnRedactions

# single-table, by skyflow ID
vault.get(GetRequest(
    table_name='table1',
    skyflow_ids=['9fac9201-7b8a-4446-93f8-5244e1213bd1'],
    columns=['card_number', 'cardholder_name'],
    column_redactions=[ColumnRedactions(column_name='card_number', redaction='MASKED')],
    limit=10, offset=0,
))

# single-table, by unique value
vault.get(GetRequest(table_name='table2', unique_values=[{'email': 'jane.doe@example.com'}]))

# multi-table batch — each GetRequestRecord carries its own table and lookup fields
vault.get(GetRequest(records=[
    GetRequestRecord(table_name='table1', skyflow_ids=['9fac9201-...'], columns=['card_number']),
    GetRequestRecord(table_name='table2', unique_values=[{'email': 'jane.doe@example.com'}]),
]))
```

There is no async variant: `get` returns its `GetResponse` directly.

Sample response:

```json
{
  "records": [
    {
      "table_name": "table1",
      "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1",
      "tokens": {
        "card_number": [ { "token": "5484-7829-1702-9110", "token_group_name": "card_number_cg", "path": null } ]
      },
      "data": { "card_number": "4111-XXXX-XXXX-1111", "cardholder_name": "John Doe" },
      "hashed_data": null,
      "http_code": 200,
      "error": null,
      "request_id": null
    }
  ]
}
```

`GetResponseRecord` carries the same fields as an insert record, plus plaintext `.data`: `.table_name`, `.skyflow_id`, `.tokens`, `.data`, `.hashed_data`, `.http_code`, `.error`, `.request_id`.

```python
for record in response.records:
    if record.error is None:
        print(record.skyflow_id, '->', record.data)
    else:
        print(record.skyflow_id, 'failed', record.http_code, record.error)
```

# Update

Update records in a table by skyflow ID, in a single API call.

> **Vault type supported:** structured (schema) vaults. See [Vault type support](#vault-type-support).

**Note:**

- `table_name` is required on the request. A record may override it with its own `table_name`, which applies to that record only.
- Every `UpdateRequestRecord` needs a non-blank `skyflow_id`.
- `data` holds the columns to change; no key or value may be blank. `tokens` is optional bring-your-own-token.
- `update_type` accepts `UpsertType.UPDATE` (merge the supplied columns) or `UpsertType.REPLACE` (overwrite the whole record). Omitting it sends no `update_type`, which the vault treats the same as an update. It is a request-level setting.

```python
from skyflow.vault.data import UpdateRequest, UpdateRequestRecord
from skyflow.utils.enums import UpsertType

request = UpdateRequest(
    table_name='table1',
    update_type=UpsertType.UPDATE,
    records=[UpdateRequestRecord(skyflow_id='9fac9201-7b8a-4446-93f8-5244e1213bd1', data={'cardholder_name': 'jane doe'})],
)
response = vault.update(request)
```

There is no async variant: `update` returns its `UpdateResponse` directly.

Sample response:

```json
{
  "records": [
    {
      "table_name": "table1",
      "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1",
      "tokens": {
        "cardholder_name": [ { "token": "f1a2b3c4-d5e6-7890-abcd-ef1234567890", "token_group_name": "deterministic_string", "path": null } ]
      },
      "data": { "cardholder_name": "Jane Doe" },
      "hashed_data": null,
      "http_code": 200,
      "error": null,
      "request_id": null
    }
  ]
}
```

Like `GetResponseRecord`, `UpdateResponseRecord` carries the insert record's fields plus `.data`: `.table_name`, `.skyflow_id`, `.tokens`, `.data`, `.hashed_data`, `.http_code`, `.error`, `.request_id`. Successes and failures come back in one `records` list, each tagged with its own `.http_code`/`.error`.

```python
for record in response.records:
    if record.error is None:
        print(record.skyflow_id, 'updated')
    else:
        print(record.skyflow_id, 'failed', record.http_code, record.error)
```

# Delete

Delete records from a table by skyflow ID or unique value, in a single API call.

> **Vault type supported:** structured (schema) vaults. See [Vault type support](#vault-type-support).

**Note:**

- `table_name` is required, and exactly one of `ids` or `unique_values` must be supplied — both, or neither, fails validation.
- `unique_values` takes the same shape as in [Get](#get): one dict per record, holding the unique column-name/value pairs that identify it.

```python
from skyflow.vault.data import DeleteRequest

request = DeleteRequest(
    table_name='table1',
    ids=['9fac9201-7b8a-4446-93f8-5244e1213bd1', 'b2308e2a-c1f5-469b-97b7-1f193159399b'],
)
response = vault.delete(request)
```

There is no async variant: `delete` returns its `DeleteResponse` directly.

Sample response:

```json
{
  "records": [
    { "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1", "http_code": 200, "error": null, "request_id": null },
    { "skyflow_id": "b2308e2a-c1f5-469b-97b7-1f193159399b", "http_code": 404, "error": "Record Not Found", "request_id": "a1b2c3d4-..." }
  ]
}
```

`DeleteResponseRecord` is flatter than the insert-shaped records above — the vault returns no data, tokens, or hashed data for a delete. Accessors: `.skyflow_id`, `.http_code`, `.error`, `.request_id`.

```python
for record in response.records:
    if record.error is None:
        print(record.skyflow_id, 'deleted')
    else:
        print(record.skyflow_id, 'failed', record.http_code, record.error)
```

# Custom Request Headers

To include custom HTTP headers on an outgoing request — bulk or unary — pass an **interceptor** via that operation's options object. The interceptor is a callable that receives a `RequestContext` and can add headers to it. The headers available are defined by the `CustomHeaderKey` enum:

| `CustomHeaderKey` | HTTP header name |
|---|---|
| `SKYFLOW_ACCOUNT_ID` | `x-skyflow-account-id` |
| `SKYFLOW_ACCOUNT_NAME` | `x-skyflow-account-name` |
| `REQUEST_ID_HEADER` | `x-request-id` |

```python
from skyflow.vault.data import BulkInsertOptions, CustomHeaderKey

def add_request_id(context):
    # context.operation ('INSERT'/'DETOKENIZE'), context.batch_index, context.total_batches
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, f'req-{context.batch_index}')

response = vault.bulk_insert(request, BulkInsertOptions(interceptor=add_request_id))
```

The interceptor runs **once per batch**, not once per bulk call — so a value generated inside it (a fresh request id, say) differs between the batches a single bulk call is split into. On a unary operation there is only ever one call, so it runs exactly once. Headers it adds are merged on top of the SDK's own headers (metrics + `Authorization`).

The same pattern applies to every operation, via its corresponding options class:

| Operation | Options class |
|---|---|
| `bulk_insert` / `bulk_insert_async` | `BulkInsertOptions` |
| `bulk_detokenize` / `bulk_detokenize_async` | `BulkDetokenizeOptions` |
| `insert` | `InsertOptions` |
| `detokenize` | `DetokenizeOptions` |
| `get` | `GetOptions` |
| `update` | `UpdateOptions` |
| `delete` | `DeleteOptions` |

# Error Handling

## Two layers of errors

This is the mental model to hold for every operation, bulk or unary:

| Layer | What it covers | How you see it |
|---|---|---|
| **Request-level** | The call could not be made or the whole call failed: invalid request shape, missing credentials, auth failure, payload over the 10,000-item limit, or a whole-call API rejection. | A raised `SkyflowError`. No results at all. |
| **Record-level** | The call succeeded, but individual records or tokens inside it did not. | A returned response. **Nothing is raised.** Each entry in `response.records` reports its own `http_code` and `error`. |

The second layer is what distinguishes `flowvault` from an all-or-nothing API: **a call that returns normally can still contain failures, and a call where every single record failed also returns normally rather than raising.** Checking only for a raised exception will silently miss failed records — always read the summary and the per-record results.

Unary operations follow the same two layers. Their records carry the same `request_id` behavior as bulk records — `None` on success, the failing call's `x-request-id` on error — the only structural difference is that unary records have no `index` (there is no batch position to report).

## Per-record success and failure

Every bulk response exposes `.summary` and `.records`. The records list has one entry per submitted item, in the order you submitted it, and each entry carries:

| Attribute | Present on | Meaning |
|---|---|---|
| `.index` | bulk only | Position of this item in the payload you submitted — use it to line results back up with your input. |
| `.http_code` | always | Per-item status. `2xx` for success; `4xx`/`5xx` for failure. |
| `.error` | failures only | Error message for this item. `None` means this item succeeded. |
| `.request_id` | failures only | The `x-request-id` of the call this item was part of — quote it in support escalations. In bulk responses, items from the same batch share one id. Present on both bulk and unary records. |

The success payload sits alongside those attributes on the same object: `.skyflow_id`/`.tokens`/`.hashed_data` (and `.data` for `get`/`update`) for record-shaped operations, `.value`/`.token_group_name`/`.metadata` for detokenize, `.skyflow_id` alone for delete.

Summaries per bulk operation:

| Response | Summary type | Fields |
|---|---|---|
| `BulkInsertResponse` | `BulkSummary` | `total_records`, `total_inserted`, `total_failed` |
| `BulkDetokenizeResponse` | `DetokenizeSummary` | `total_tokens`, `total_detokenized`, `total_failed` |

A unary response has no summary and no `.index` — just `.records`, in submitted order, with `.http_code`, `.error`, and `.request_id` on each entry alongside that operation's payload.

The idiomatic way to consume a bulk response:

```python
response = vault.bulk_insert(request)

print('inserted', response.summary.total_inserted, 'of', response.summary.total_records)

for record in response.records:
    if record.error is None:
        print('row', record.index, '->', record.skyflow_id)
    else:
        print('row', record.index, 'failed', record.http_code, record.error, '(request_id', record.request_id, ')')
```

## Catching SkyflowError

`SkyflowError` covers the request-level layer only — client-side validation errors and whole-call API errors. It comes from `common`, so it is the same exception type `skyvault` raises.

```python
from skyflow.error import SkyflowError

try:
    response = vault.bulk_insert(request)
    # reaching here means the CALL succeeded — individual records may still have failed
except SkyflowError as e:
    print('HTTP code :', e.http_code)
    print('Message   :', e.message)
    print('Request ID:', e.request_id)
    print('Details   :', e.details)
except Exception as e:
    print('Unexpected error:', e)
```

The async variants raise the same `SkyflowError` from the awaited call:

```python
try:
    response = await vault.bulk_insert_async(request)
except SkyflowError as e:
    print('bulk insert failed:', e.message)
```

## SkyflowError properties

| Property | Attribute | Description |
|---|---|---|
| HTTP status code | `.http_code` | Integer status code (e.g. `400`, `404`, `500`). |
| Message | `.message` | Human-readable description of the error. |
| gRPC code | `.grpc_code` | gRPC status code from the server. |
| HTTP status string | `.http_status` | Status string from the server. |
| Request ID | `.request_id` | The `x-request-id` header — useful for support escalations. |
| Details | `.details` | Additional error context from the server. Empty for validation errors, `None` if the server response omitted the field. |

**Validation errors** (table name at the wrong level, empty token list, payload over 10,000 items, and similar) are raised before any network call, with `http_code` `400`. **API errors** are returned by the Skyflow server and have all fields populated from the response body and headers.

## Retrying the failed records

Because bulk failures are reported per record, a partial failure can be retried without resubmitting the whole payload. Each bulk response exposes a retry helper that filters its records down to the ones worth resending — **server-side failures (HTTP 500–599), excluding 529**, which is a permanent capacity-limit code:

| Response | Helper | Returns |
|---|---|---|
| `BulkInsertResponse` | `records_to_retry()` | `list[BulkInsertRequestRecord]` — your original record objects, ready to resubmit |
| `BulkDetokenizeResponse` | `tokens_to_retry()` | `list[str]` — the tokens to resubmit |

```python
response = vault.bulk_insert(request)

retryable = response.records_to_retry()
if retryable:
    retry_response = vault.bulk_insert(BulkInsertRequest(records=retryable))
```

Client-side (`4xx`) failures are deliberately excluded — those need a fix to the data, not a retry. This is separate from the transport-level `max_retries` setting in [Timeouts and retries](#timeouts-and-retries), which retries whole HTTP attempts and is off by default. Unary operations have no retry helper — filter `response.records` yourself on `record.http_code`.

# Samples

Runnable examples live in [samples/](samples/) — one file per operation, with sync/async pairs for the bulk ops, plus custom-header, timeout/retry, and service-account examples. See [samples/README.md](samples/README.md) to run them.
