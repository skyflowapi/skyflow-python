# flowvault Python SDK — Request / Response shapes

JSON shapes as the **Python** flowvault SDK currently produces them, for manual comparison
against the Java FlowDB contract. Keys are **snake_case**. `tokens` and `hashed_data` are
normalized to typed lists; detokenize `metadata` is normalized to `{skyflow_id, table_name}`.

> Requests below are shown as the JSON equivalent of the SDK request objects (constructor args).
> Request wire bodies are built separately by the generated client and are not shown here.
> `//` comments name the Python data class each object maps to (Python responses use plain dicts,
> so the Java equivalent class is noted for those). Blocks are `jsonc` (JSON + comments).

**Parity status per op**

| Operation | In Java contract? | Response shape |
|-----------|-------------------|----------------|
| insert / get / delete / detokenize / query | yes | new unified `records` list |
| bulk_insert / bulk_detokenize | yes | `summary` + `records` |
| update | **no (Python-only)** | old split `records` + `errors` |

---

## Unary — insert

**Request** — `InsertRequest(records: List[InsertRequestRecord], table_name=None, upsert=None)`
```jsonc
// InsertRequest
{
  "table_name": "cards",
  "upsert": { "unique_columns": ["card_number"], "update_type": "UPDATE" }, // UpsertOptions(unique_columns, update_type)
  "records": [
    // InsertRequestRecord(data, table_name=None, tokens=None, upsert=None)
    { "data": { "card_number": "4111111111111111", "cardholder_name": "john doe" } }
  ]
}
```
Per-record table_name/upsert instead of request-level (exactly one level, never both); `tokens` is optional BYOT:
```jsonc
// InsertRequest
{
  "records": [
    // InsertRequestRecord
    { "data": { "email": "jane@example.com" }, "table_name": "contacts",
      "tokens": { "email": "my-own-token" },
      "upsert": { "unique_columns": ["email"], "update_type": "REPLACE" } } // upsert: UpsertOptions(unique_columns, update_type)
  ]
}
```
> `update_type` is an `UpsertType` enum (`.value` is the Java `"UPDATE"`/`"REPLACE"` string).

**Response** — `InsertResponse(records)`
```jsonc
// InsertResponse
{
  "records": [
    // record: plain dict (Java: InsertResponseRecord)
    {
      "table_name": "cards",
      "skyflow_id": "f1714ef8-8deb-489a-a18d-77e0e007f403",
      "tokens": {
        // each entry: plain dict (Java: Token)
        "ssn": [
          { "token": "3340-9871-4511-3462", "token_group_name": "deterministic_string", "path": null },
          { "token": "7823-1234-5678-9012", "token_group_name": "random_string", "path": null }
        ]
      },
      "hashed_data": { "ssn": [ { "data": "2f3fd7b1d46c...", "hash_name": "hash1" } ] }, // entry Java: HashedValue
      "http_code": 200,
      "error": null
    },
    {
      "table_name": null,
      "skyflow_id": null,
      "tokens": null,
      "hashed_data": null,
      "http_code": 400,
      "error": "Invalid request. Table name table not present for record. Specify a valid table name."
    }
  ]
}
```
> Insert records omit `data` (unlike `get`, which includes it).

---

## Unary — get

Two **mutually exclusive** request modes.

**Request — single-table mode** — `GetRequest(table_name, ids, unique_values, columns, column_redactions, limit, offset)`
```jsonc
// GetRequest
{
  "table_name": "persons",
  "ids": ["9f5b8e6e-..."],
  "unique_values": [ { "email": "john@example.com" } ],
  "columns": ["name", "email"],
  "column_redactions": [ { "column_name": "email", "redaction": "MASKED" } ], // entry: ColumnRedaction(column_name, redaction)
  "limit": 25,
  "offset": 0
}
```
**Request — multi-table batch mode** — `GetRequest(records=[GetRecordRequest(table_name, ids, columns, column_redactions: List[ColumnRedaction], unique_values)])` (no `limit`/`offset`; single-table fields must be unset)
```jsonc
// GetRequest
{
  "records": [
    // GetRecordRequest(table_name, ids=None, columns=None, column_redactions=None, unique_values=None)
    { "table_name": "persons", "ids": ["9f5b8e6e-..."], "columns": ["name"],
      "column_redactions": [], "unique_values": [] },
    { "table_name": "cards", "unique_values": [ { "email": "john@example.com" } ] }
  ]
}
```

**Response** — `GetResponse(records)` (same per-record builder as insert, but `data` is included)
```jsonc
// GetResponse
{
  "records": [
    // record: plain dict (Java: GetResponseRecord / shared Record)
    {
      "table_name": "persons",
      "skyflow_id": "9f5b8e6e-...",
      "tokens": { "card_number": [ { "token": "5301-6390-5701-2392", "token_group_name": "det", "path": null } ] }, // entry Java: Token
      "data": { "name": "John Doe", "email": "a1b2c3d4" },
      "hashed_data": { "email": [ { "data": "2f3fd7b1d46c...", "hash_name": "hash1" } ] }, // entry Java: HashedValue
      "http_code": 200,
      "error": null
    },
    {
      "table_name": null,
      "skyflow_id": null,
      "tokens": null,
      "data": null,
      "hashed_data": null,
      "http_code": 404,
      "error": "Record not found"
    }
  ]
}
```

---

## Unary — delete

**Request** — `DeleteRequest(table_name, ids, unique_values)`
```jsonc
// DeleteRequest
{ "table_name": "persons", "ids": ["9f5b8e6e-..."], "unique_values": [ { "email": "john@example.com" } ] }
```

**Response** — `DeleteResponse(records)`
```jsonc
// DeleteResponse
{
  "records": [
    // record: plain dict (Java: DeleteResponseRecord / shared Record)
    { "skyflow_id": "9f5b8e6e-...", "http_code": 200, "error": null },
    { "skyflow_id": null, "http_code": 404, "error": "Record not found" }
  ]
}
```

---

## Unary — detokenize

**Request** — `DetokenizeRequest(tokens, token_group_redactions)`
```jsonc
// DetokenizeRequest
{
  "tokens": ["12393023", "7c4a0139-9033-40ae-b41f-f3837976721"],
  "token_group_redactions": [ { "token_group_name": "deterministic_string", "redaction": "MASKED" } ] // entry: dict {token_group_name, redaction} (Java: TokenGroupRedactions)
}
```

**Response** — `DetokenizeResponse(records)`
```jsonc
// DetokenizeResponse
{
  "records": [
    // record: plain dict (Java: DetokenizeResponseRecord)
    {
      "token": "12393023",
      "token_group_name": "deterministic_string",
      "value": "john@example.com",
      "metadata": { "skyflow_id": "3ac0424e-fe45-43a9-9193-2e6d2913cbd2", "table_name": "table1" }, // dict (Java: DetokenizeMetadata)
      "http_code": 200,
      "error": null
    },
    {
      "token": "7c4a0139-9033-40ae-b41f-f3837976721",
      "token_group_name": null,
      "value": null,
      "metadata": null,
      "http_code": 404,
      "error": "Detokenize failed. Token 7c4a0139-... is invalid. Specify a valid token."
    }
  ]
}
```
> Note: the Java contract's new `DetokenizeResponseRecord` omits `value`; Python **keeps** it.

---

## Unary — query

**Request** — `QueryRequest(query)`
```jsonc
// QueryRequest
{ "query": "SELECT * FROM persons WHERE skyflow_id = '9f5b8e6e-...'" }
```

**Response** — `QueryResponse(records, metadata)`
```jsonc
// QueryResponse
{
  "records": [
    // record: plain dict {data} (Java: QueryResponseRecord)
    { "data": { "skyflow_id": "9f5b8e6e-...", "name": "John Doe", "email": "a1b2c3d4" } }
  ],
  "metadata": { "columns": ["skyflow_id", "name", "email"] } // dict (Java: QueryResponseMetadata)
}
```
On a failed call (`metadata` is `null`):
```jsonc
// QueryResponse
{ "records": [ { "data": null, "http_code": 400, "error": "bad query" } ], "metadata": null }
```

---

## Bulk — bulk_insert / bulk_insert_async

**Request** — `BulkInsertRequest(records: List[BulkInsertRequestRecord], table_name=None, upsert=None)`
**Options** (optional 2nd arg) — `bulk_insert(request, options: BulkInsertOptions = None)` — see [Custom request headers](#custom-request-headers).

> The bulk record type is `BulkInsertRequestRecord(data, table_name=None, tokens=None, upsert=None)` — same fields as
> Java's `BulkInsertRequestRecord extends InsertRequestRecord`, `tokens` included (BYOT).
```jsonc
// BulkInsertRequest
{
  "table_name": "cards",
  "upsert": { "unique_columns": ["card_number"], "update_type": "UPDATE" }, // UpsertOptions
  "records": [
    // BulkInsertRequestRecord(data, table_name=None, upsert: UpsertOptions=None)
    { "data": { "card_number": "4111111111111111", "cardholder_name": "john doe" } },
    { "data": { "email": "jane@example.com" }, "table_name": "contacts",
      "upsert": { "unique_columns": ["email"] } } // UpsertOptions
  ]
}
```

**Response** — `BulkInsertResponse(summary, records)`
```jsonc
// BulkInsertResponse
{
  "summary": { "total_records": 2, "total_inserted": 1, "total_failed": 1 }, // BulkSummary
  "records": [
    // record: plain dict (Java: BulkInsertResponseRecord)
    {
      "index": 0,
      "request_id": null,
      "table_name": "cards",
      "skyflow_id": "9fac9201-7b8a-4446-93f8-5244e1213bd1",
      "tokens": { "card_number": [ { "token": "5484-7829-1702-9110", "token_group_name": "card_number_cg", "path": null } ] }, // entry Java: Token
      "data": { "card_number": "4111-1111-1111-1111" },
      "hashed_data": { "card_number": [ { "data": "b6e6d...c3f9", "hash_name": "hash1" } ] }, // entry Java: HashedValue
      "http_code": 200,
      "error": null
    },
    {
      "index": 1,
      "request_id": "a1b2c3d4-...",
      "table_name": null,
      "skyflow_id": null,
      "tokens": null,
      "data": null,
      "hashed_data": null,
      "http_code": 400,
      "error": "Insert failed. Column email is invalid."
    }
  ]
}
```
> `response.records_to_retry()` returns the original `BulkInsertRequestRecord`s whose `http_code` is 500–599 (excluding 529). Not part of the JSON.

---

## Bulk — bulk_detokenize / bulk_detokenize_async

**Request** — `BulkDetokenizeRequest(tokens, token_group_redactions)`
**Options** (optional 2nd arg) — `bulk_detokenize(request, options: BulkDetokenizeOptions = None)` — see [Custom request headers](#custom-request-headers).
```jsonc
// BulkDetokenizeRequest
{
  "tokens": ["5479-4229-4622-1393", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
  "token_group_redactions": [ { "token_group_name": "card_number_cg", "redaction": "MASKED" } ] // entry: dict {token_group_name, redaction} (Java: TokenGroupRedactions)
}
```

**Response** — `BulkDetokenizeResponse(summary, records)`
```jsonc
// BulkDetokenizeResponse
{
  "summary": { "total_tokens": 2, "total_detokenized": 1, "total_failed": 1 }, // DetokenizeSummary
  "records": [
    // record: plain dict (Java: BulkDetokenizeResponseRecord)
    {
      "index": 0,
      "request_id": null,
      "value": "4111111111111111",
      "token_group_name": "card_number_cg",
      "metadata": { "skyflow_id": "9fac9201-...", "table_name": "table1" }, // dict (Java: DetokenizeMetadata)
      "http_code": 200,
      "token": "5479-4229-4622-1393",
      "error": null
    },
    {
      "index": 1,
      "request_id": "a1b2c3d4-...",
      "value": null,
      "token_group_name": null,
      "metadata": null,
      "http_code": 404,
      "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "error": "Token Not Found"
    }
  ]
}
```
> `response.tokens_to_retry()` returns the original token strings whose `http_code` is 500–599 (excluding 529).

---

## Python-only ops (NOT in the Java FlowDB contract — still the OLD split shape)

### update

**Request** — `UpdateRequest(records: list[dict], table_name=None, update_type=None)`
```jsonc
// UpdateRequest  (records are plain dicts, not a typed record class)
{
  "table_name": "persons",
  "update_type": "REPLACE",
  "records": [
    { "skyflow_id": "9f5b8e6e-...", "data": { "name": "Jane" }, "tokens": { "ssn": "tok" }, "table_name": null }
  ]
}
```
> The regenerated `update_records` endpoint does not accept `update_type`; the field is validated
> but not forwarded.

**Response** — `UpdateResponse(records, errors)` — old split shape (`records` = successes, plus `errors`)
```jsonc
// UpdateResponse
{
  "records": [ { "request_index": 0, "skyflow_id": "9f5b8e6e-...", "ssn": "tok1", "data": { "name": "Jane" } } ],
  "errors": [ { "request_index": 1, "error": "not found", "code": 404, "request_id": "req-..." } ]
}
```

---

## Custom request headers

Bulk operations (`bulk_insert`/`bulk_insert_async`, `bulk_detokenize`/`bulk_detokenize_async`) accept an
optional `options` object carrying an **interceptor** — a callable run **once per batch** that can add
custom headers to that batch's outgoing request (mirrors Java's `RequestInterceptor`).

- `BulkInsertOptions(interceptor=None)` / `BulkDetokenizeOptions(interceptor=None)` — `interceptor: Callable[[RequestContext], None]`
- `RequestContext(operation, batch_index, total_batches)` — `.operation` (`"INSERT"` / `"DETOKENIZE"`),
  `.batch_index` (0-based, `-1` when not batched), `.total_batches`, `.add_header(key, value)`, `.headers`
- `CustomHeaderKey` enum — allowed header keys: `SKYFLOW_ACCOUNT_ID` (`x-skyflow-account-id`),
  `SKYFLOW_ACCOUNT_NAME` (`x-skyflow-account-name`), `REQUEST_ID_HEADER` (`x-request-id`)

```python
from skyflow_flowvault.vault.data import BulkInsertOptions, CustomHeaderKey

def add_request_id(context):
    context.add_header(CustomHeaderKey.REQUEST_ID_HEADER, f"req-{context.batch_index}")

vault.bulk_insert(insert_request, BulkInsertOptions(interceptor=add_request_id))
```

> The interceptor runs once per batch, so a value it generates (e.g. a fresh request id) differs
> between the batches a single bulk call is split into. Headers added by the interceptor are merged
> on top of the SDK's own headers (metrics + `Authorization`).

---

## Timeouts & retries (Java `VaultConfig` parity, flowvault only)

Full parity with Java's `VaultConfig` HTTP settings, exposed at **two levels** — per-vault (keys on the
config dict passed to `add_vault_config`) and client-wide (chainable builder methods). Precedence is
resolved **per field: per-vault → client-wide → SDK default**.

| Per-vault key | Builder method | Type | Default | Meaning |
|---|---|---|---|---|
| `timeout` | `.timeout(s)` | seconds | `60` | Overall call ceiling, bounds the whole call incl. retries + backoff. |
| `connect_timeout` | `.connect_timeout(s)` | seconds | `10` | Per-attempt connection-establishment timeout. |
| `read_timeout` | `.read_timeout(s)` | seconds | `10` | Per-attempt response-read timeout. |
| `write_timeout` | `.write_timeout(s)` | seconds | `10` | Per-attempt request-write timeout. |
| `max_retries` | `.max_retries(n)` | int ≥ 0 | `0` | Retry attempts after the first failure. `0` = opt-in off. |
| `initial_retry_delay_millis` | `.initial_retry_delay_millis(ms)` | int ≥ 0 | `500` | Backoff before the first retry. |
| `max_retry_delay_millis` | `.max_retry_delay_millis(ms)` | int ≥ 0 | `2000` | Ceiling the exponential backoff grows to. |
| `vault_url` | *(per-vault only)* | string | — | Overrides the URL derived from `cluster_id`/`env`. |

```python
Skyflow.builder()
    .timeout(60).max_retries(3).initial_retry_delay_millis(500).max_retry_delay_millis(4000)  # client-wide
    .add_vault_config({
        "vault_id": "<VAULT_ID>", "cluster_id": "<CLUSTER_ID>", "env": Env.PROD,
        "credentials": {...},
        "timeout": 30, "connect_timeout": 5, "read_timeout": 20, "max_retries": 2,  # per-vault overrides
    })
    .build()
```

> **Implementation (mirrors Java exactly, no generated-code edits).** Like Java — which hand-writes
> `SkyflowRetryInterceptor` and injects a configured `OkHttpClient` into the generated client — flowvault
> injects a custom **httpx transport** (`RetryTransport`, httpx's equivalent of an OkHttp interceptor)
> plus an `httpx.Timeout` into the generated `SkyflowAuth(httpx_client=...)`. The transport retries on
> `408 / 429 / 5xx` with exponential backoff + jitter (`JITTER_FACTOR` 0.2), honoring `initial`/`max`
> delay bounds and the overall `timeout` as a deadline across attempts. `max_retries` = the actual
> number of retries.
>
> **Differences from Java:** the overall `timeout` is enforced at attempt boundaries (httpx has no
> socket-level call timeout), and `vault_url` is per-vault only (Java exposes it the same way). Every
> value is validated at `add_vault_config` / on the builder setter (`SkyflowError` on a bad value).
