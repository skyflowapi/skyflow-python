# Skyflow Python SDK — Samples

Runnable examples for the Skyflow Python SDK, grouped by area. Start with the [README](../README.md) and [API Reference](../docs/api_reference.md) for full documentation.

## Prerequisites

- Python 3.9 or above
- The SDK installed: `pip install skyflow`
- A Skyflow account, a vault, and a service account (see [Before you begin](../README.md#before-you-begin))
- The values listed in [`.env.example`](.env.example): `vault_id`, `cluster_id`, `env`, and one credential (API key, bearer token, or service-account credentials)

## Configure

Copy the env template and fill in your values:

```bash
cp .env.example .env
```

The samples ship with inline `<PLACEHOLDER>` strings (for example `<YOUR_VAULT_ID>`). You can either:

1. **Replace the placeholders** directly in the sample file you want to run, or
2. **Load from `.env`** by adding the following near the top of the sample (`python-dotenv` is already a SDK dependency):

   ```python
   import os
   from dotenv import load_dotenv

   load_dotenv()
   vault_id = os.getenv('SKYFLOW_VAULT_ID')
   # ...use os.getenv(...) for the other values
   ```

> Never commit a filled-in `.env` or any real credentials.

## Run a sample

```bash
python samples/vault_api/insert_records.py
```

## What's here

### `vault_api/`
Core vault data operations.

| Sample | Demonstrates |
|--------|--------------|
| `client_operations.py` | Building and managing the Skyflow client |
| `credentials_options.py` | The different credential types |
| `insert_records.py` | Inserting and tokenizing records (`continue_on_error`) |
| `insert_byot.py` | Bring-your-own-token inserts |
| `get_records.py` | Getting records by Skyflow ID |
| `get_column_values.py` | Getting records by column name/values |
| `update_record.py` | Updating a record |
| `delete_records.py` | Deleting records |
| `query_records.py` | SQL queries |
| `detokenize_records.py` | Detokenizing tokens |
| `tokenize_records.py` | Retrieving existing tokens |
| `upload_file.py` | Uploading a file to a record |
| `invoke_connection.py` | Invoking a Skyflow Connection |

### `detect_api/`
Skyflow Detect (de-identification / re-identification).

| Sample | Demonstrates |
|--------|--------------|
| `deidentify_text.py` | De-identifying text |
| `reidentify_text.py` | Re-identifying text |
| `deidentify_file.py` | De-identifying a file |
| `deidentify_file_concurrent.py` | Running a file de-identification on a background thread (thread-based concurrency, not asyncio) |
| `get_detect_run.py` | Polling a file de-identification run by `run_id` |

### `service_account/`
Bearer-token and signed-data-token generation.

| Sample | Demonstrates |
|--------|--------------|
| `token_generation_example.py` | Generating a bearer token |
| `scoped_token_generation_example.py` | Tokens scoped to specific roles |
| `token_generation_with_context_example.py` | Tokens with context (`ctx`) |
| `signed_token_generation_example.py` | Signed data tokens |
| `bearer_token_expiry_example.py` | Handling token expiry / regeneration |
