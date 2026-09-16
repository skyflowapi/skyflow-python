# Skyflow FlowVault Python SDK

The `flowvault` module is a Skyflow Python SDK for vault operations. It shares its client, credentials, and configuration with the [skyvault SDK](../skyvault/README.md) (both depend on the `common` module) but exposes a different, narrower surface: **unary** vault operations — insert, get, update, delete, and detokenize.

> Meant for **FlowVault** vaults.

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
  - [Thread safety and resource lifecycle](#thread-safety-and-resource-lifecycle)
  - [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults)
- [VaultController — Unary operations](#vaultcontroller--unary-operations)
  - [Vault type support](#vault-type-support)
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
- Perform unary Vault API operations — insert, get, update, delete, and detokenize — a single API call each. See [VaultController — Unary operations](#vaultcontroller--unary-operations).
- **Per-record reporting, not all-or-nothing.** A call succeeds as a call even when individual records fail; every response reports the outcome of each individual record or token. See [Error Handling](#error-handling).

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

> **Do not install this alongside the main `skyflow` SDK.** This package and the main [skyflow SDK](../skyvault/README.md) (published to PyPI as `skyflow`) both ship the same top-level `skyflow` import package, so installing both in one environment makes them shadow each other — whichever was installed last wins, and imports resolve to the wrong SDK. Pick the one you need per environment, and if you need both, keep them in separate virtual environments.

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

When retries are enabled, retryable responses (HTTP `408` / `429` / `5xx`) are retried with exponential backoff and jitter, bounded by the `initial`/`max` delays and the overall `timeout`.

## Logging

The SDK logs at `LogLevel.ERROR` by default. Levels rank `DEBUG` < `INFO` < `WARN` < `ERROR` < `OFF`; setting a level prints that level and everything above it. Change it with `Skyflow.builder().set_log_level(LogLevel.DEBUG)`.

## Thread safety and resource lifecycle

- **Thread safety** — `Skyflow` and every `VaultController` it hands out are meant to be built once and reused for the application's lifetime; the underlying HTTP client is reused across calls rather than recreated per request.

## Schema vs. schemaless vaults

Which operations make sense depends on whether the vault is **structured** (has a schema — tables and columns) or **schemaless** (stores standalone tokens with no table structure): the record operations (`insert`, `get`, `update`, `delete`) address a table's columns and so need a structured vault, while `detokenize` needs only the token itself and works against either kind. See [Vault type support](#vault-type-support) for the per-operation breakdown.

# VaultController — Unary operations

`VaultController` is returned by `skyflow_client.vault(...)` and exposes these vault operations. Each sends exactly one API call and hands the result straight back:

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `insert(request)` | `InsertRequest`, optional `InsertOptions` | `InsertResponse` | Insert records, optionally across multiple tables, in one call |
| `detokenize(request)` | `DetokenizeRequest`, optional `DetokenizeOptions` | `DetokenizeResponse` | Detokenize tokens, optionally with a redaction override per token group |
| `get(request)` | `GetRequest`, optional `GetOptions` | `GetResponse` | Read records by skyflow ID or unique value, optionally with a redaction override per column |
| `update(request)` | `UpdateRequest`, optional `UpdateOptions` | `UpdateResponse` | Update records by skyflow ID |
| `delete(request)` | `DeleteRequest`, optional `DeleteOptions` | `DeleteResponse` | Delete records by skyflow ID or unique value |

Each method also accepts an optional options object (`InsertOptions`, `DetokenizeOptions`, `GetOptions`, `UpdateOptions`, `DeleteOptions`) — see [Custom Request Headers](#custom-request-headers).

## Vault type support

The same distinction as [Schema vs. schemaless vaults](#schema-vs-schemaless-vaults) applies. Four of the five unary operations address records inside a table, so they only make sense against a structured vault:

| Operation | Supported on |
|---|---|
| `insert` | Structured (schema) vaults — inserts into a table's columns. |
| `get` | Structured vaults — reads a table's records by skyflow ID or unique value. |
| `update` | Structured vaults — updates a table's records by skyflow ID. |
| `delete` | Structured vaults — deletes a table's records. |
| `detokenize` | Both — detokenizing only needs the token itself, not a table, so it works regardless of which kind of vault the token came from. |

# Insert

Insert records in a single API call. Each record is an `InsertRequestRecord` with its own `data` and, optionally, its own `table_name`, `tokens`, and `upsert`.

> **Vault type supported:** structured (schema) vaults. See [Vault type support](#vault-type-support).

**Note:**

- `table_name`/`upsert` follow a one-level rule: on the request (applies to all records) or on every record — never both.
- `tokens` is optional bring-your-own-token; when supplied, the map must not be empty and no key or value may be blank.

```python
from skyflow.vault.data import InsertRequest, InsertRequestRecord, UpsertOptions
from skyflow.utils.enums import UpsertType

vault = skyflow_client.vault('<VAULT_ID>')  # skyflow_client from Quickstart

# Insert several records into one table — set table_name once on the request
request = InsertRequest(
    table_name='cards',
    records=[
        InsertRequestRecord(data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'}),
        InsertRequestRecord(data={'card_number': '4222222222222222', 'cardholder_name': 'jane doe'}),
    ],
)
response = vault.insert(request)
```

To put the table name on each record instead — the same one-level rule — drop the request-level `table_name` and set it on **every** record. This is also how you insert across different tables in one call, and where per-record `upsert` goes:

```python
request = InsertRequest(records=[
    # table_name lives on each record here
    InsertRequestRecord(table_name='table1', data={'card_number': '4111111111111111', 'cardholder_name': 'john doe'}),
    InsertRequestRecord(
        table_name='table2',
        data={'email': 'jane.doe@example.com'},
        upsert=UpsertOptions(unique_columns=['email'], update_type=UpsertType.UPDATE),
    ),
])
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
      "data": { "card_number": "4111111111111111", "cardholder_name": "john doe" },
      "hashed_data": { "card_number": [ { "data": "b6e6d...c3f9", "hash_name": "hash1" } ] },
      "http_code": 200,
      "error": null,
      "request_id": null
    },
    {
      "table_name": "cards",
      "skyflow_id": "1c7e4f02-9a3b-4d18-8f21-6b0c9d5e3a44",
      "tokens": {
        "card_number": [ { "token": "6011-3821-4490-7752", "token_group_name": "card_number_cg", "path": null } ]
      },
      "data": { "card_number": "4222222222222222", "cardholder_name": "jane doe" },
      "hashed_data": { "card_number": [ { "data": "1a2b3...9f0e", "hash_name": "hash1" } ] },
      "http_code": 200,
      "error": null,
      "request_id": null
    }
  ]
}
```

The records come back in the order you submitted them. `request_id` is `None` on success and the failing call's `x-request-id` on error. `.tokens` maps each column to a **list** of `Token` objects — one entry per token group configured on that column — each with `.token`, `.token_group_name`, and `.path` (the location within a structured column's value the token came from, e.g. `"phone_numbers[0].type"`; `None` for a flat column). Insert records also carry `.data`, the stored column values the vault returns.

```python
for record in response.records:
    if record.error is None:
        print(record.skyflow_id, record.tokens)
    else:
        print('insert failed', record.http_code, record.error)
```

Accessors on each `InsertResponseRecord`: `.table_name`, `.skyflow_id`, `.tokens`, `.data`, `.hashed_data`, `.http_code`, `.error`, `.request_id`.

# Detokenize

Detokenize tokens in a single API call, optionally overriding the redaction applied per token group via `token_group_redactions`.

> **Vault type supported:** both. See [Vault type support](#vault-type-support).

**Note:**

- `tokens` is required and must not be empty, and no entry may be blank.
- `token_group_redactions` is optional; when supplied, each entry needs a non-blank `token_group_name` and `redaction`. Entries are `TokenGroupRedactions` objects.

```python
from skyflow.vault.data import DetokenizeRequest, TokenGroupRedactions

vault = skyflow_client.vault('<VAULT_ID>')  # skyflow_client from Quickstart

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

`record.metadata` is a typed `DetokenizeResponseRecordMetadata` with `.skyflow_id` / `.table_name` (`None` on records that errored).

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

vault = skyflow_client.vault('<VAULT_ID>')  # skyflow_client from Quickstart

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

vault = skyflow_client.vault('<VAULT_ID>')  # skyflow_client from Quickstart

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

vault = skyflow_client.vault('<VAULT_ID>')  # skyflow_client from Quickstart

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

To include custom HTTP headers on an outgoing request, pass an **interceptor** via that operation's options object. The interceptor is a callable that receives a `RequestContext` and can add headers to it. The headers available are defined by the `CustomHeaderKey` enum:

| `CustomHeaderKey` | HTTP header name |
|---|---|
| `SKYFLOW_ACCOUNT_ID` | `x-skyflow-account-id` |
| `SKYFLOW_ACCOUNT_NAME` | `x-skyflow-account-name` |
| `REQUEST_ID_HEADER` | `x-request-id` |

```python
from skyflow.vault.data import InsertOptions, CustomHeaderKey

def add_request_id(context):
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, 'req-001')

response = vault.insert(request, InsertOptions(interceptor=add_request_id))
```

The interceptor runs once per call. Headers it adds are merged on top of the SDK's own headers (metrics + `Authorization`).

The same pattern applies to every operation, via its corresponding options class:

| Operation | Options class |
|---|---|
| `insert` | `InsertOptions` |
| `detokenize` | `DetokenizeOptions` |
| `get` | `GetOptions` |
| `update` | `UpdateOptions` |
| `delete` | `DeleteOptions` |

# Error Handling

## Two layers of errors

This is the mental model to hold for every operation:

| Layer | What it covers | How you see it |
|---|---|---|
| **Request-level** | The call could not be made or the whole call failed: invalid request shape, missing credentials, auth failure, or a whole-call API rejection. | A raised `SkyflowError`. No results at all. |
| **Record-level** | The call succeeded, but individual records or tokens inside it did not. | A returned response. **Nothing is raised.** Each entry in `response.records` reports its own `http_code` and `error`. |

The second layer is what distinguishes `flowvault` from an all-or-nothing API: **a call that returns normally can still contain failures, and a call where every single record failed also returns normally rather than raising.** Checking only for a raised exception will silently miss failed records — always read the per-record results.

Each record carries its own `request_id` — `None` on success, the failing call's `x-request-id` on error.

## Per-record success and failure

Every response exposes `.records`. The records list has one entry per submitted item, in the order you submitted it, and each entry carries:

| Attribute | Present on | Meaning |
|---|---|---|
| `.http_code` | always | Per-item status. `2xx` for success; `4xx`/`5xx` for failure. |
| `.error` | always | Error message for this item, populated only on failure — `None` means this item succeeded. |
| `.request_id` | always | The `x-request-id` of the call this item was part of, populated only on failure (`None` on success) — quote it in support escalations. |

The success payload sits alongside those attributes on the same object: `.skyflow_id`/`.tokens`/`.data`/`.hashed_data` for record-shaped operations (`insert`, `get`, `update`), `.value`/`.token_group_name`/`.metadata` for detokenize, `.skyflow_id` alone for delete.

A response has just `.records`, in submitted order, with `.http_code`, `.error`, and `.request_id` on each entry alongside that operation's payload.

The idiomatic way to consume a response:

```python
response = vault.insert(request)

for record in response.records:
    if record.error is None:
        print(record.skyflow_id)
    else:
        print('failed', record.http_code, record.error, '(request_id', record.request_id, ')')
```

## Catching SkyflowError

`SkyflowError` covers the request-level layer only — client-side validation errors and whole-call API errors. It comes from `common`, so it is the same exception type `skyvault` raises.

```python
from skyflow.error import SkyflowError

try:
    response = vault.insert(request)
    # reaching here means the CALL succeeded — individual records may still have failed
except SkyflowError as e:
    print('HTTP code :', e.http_code)
    print('Message   :', e.message)
    print('Request ID:', e.request_id)
    print('Details   :', e.details)
except Exception as e:
    print('Unexpected error:', e)
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

**Validation errors** (table name at the wrong level, empty token list, and similar) are raised before any network call, with `http_code` `400`. **API errors** are returned by the Skyflow server and have all fields populated from the response body and headers.

## Retrying the failed records

Because failures are reported per record, a partial failure can be retried without resubmitting the whole payload. Resend only the records worth retrying — **server-side failures (HTTP 500–599), excluding 529**, which is a permanent capacity-limit code. Client-side (`4xx`) failures are deliberately excluded — those need a fix to the data, not a retry. This is separate from the transport-level `max_retries` setting in [Timeouts and retries](#timeouts-and-retries), which retries whole HTTP attempts and is off by default.

Records come back in input order, so you can filter `response.records` yourself with this predicate:

```python
def is_retryable(http_code):
    return isinstance(http_code, int) and 500 <= http_code <= 599 and http_code != 529
```

For `insert` — and likewise `update`, `get`, and `delete` — correlate each response record back to your input by position, then resubmit the retryable ones:

```python
request = InsertRequest(table_name='cards', records=[...])
response = vault.insert(request)

retryable = [
    request.records[i]
    for i, record in enumerate(response.records)
    if is_retryable(record.http_code)
]
if retryable:
    retry_response = vault.insert(InsertRequest(table_name='cards', records=retryable))
```

> **Make insert retries idempotent.** A record can succeed server-side even when the response never reaches you — a dropped connection, or a `5xx` returned after the row was already written — so a blind resubmit can create a duplicate. Guard against it with `upsert` on a unique column, kept at the same level as `table_name`: a retried record then updates the existing row instead of inserting a second one.

For `detokenize`, each response record carries its own `.token`, so filter on that directly — no position bookkeeping needed:

```python
response = vault.detokenize(request)

retry_tokens = [record.token for record in response.records if is_retryable(record.http_code)]
if retry_tokens:
    retry_response = vault.detokenize(DetokenizeRequest(tokens=retry_tokens))
```

# Samples

Runnable examples live in [samples/](samples/) — one file per operation, plus custom-header, timeout/retry, and service-account examples. See [samples/README.md](samples/README.md) to run them.
