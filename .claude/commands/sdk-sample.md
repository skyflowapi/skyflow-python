---
name: sdk-sample
description: Generate a Skyflow Python SDK sample file for a vault feature or service account operation. Verified runnable after creation.
paths:
  - samples/**/*.py
---

Create a Skyflow Python SDK sample file demonstrating: $ARGUMENTS

## File placement

| Feature type | Directory |
|---|---|
| Vault ops (insert/get/update/delete/query/tokenize/upload_file) | `samples/vault_api/` |
| Service account auth (bearer token, signed data tokens) | `samples/service_account/` |
| Connection | `samples/connection/` |
| Detect (deidentify/reidentify text and files) | `samples/detect_api/` |

File name: `<feature_name>.py` (snake_case)

## Structure (follow this order)

1. Module-level docstring describing what the sample demonstrates
2. Imports — only from `skyflow.*`; never from `skyflow.generated.*`
3. Credentials dict — choose based on feature:
   - **Vault ops / Detect:** `credentials = {'credentials_string': '<YOUR_CREDENTIALS_STRING>'}` or `{'api_key': '<YOUR_API_KEY>'}`
   - **Service account:** pass the path to a credentials JSON file or a credentials string
4. Vault / connection config dict with `vault_id`, `cluster_id`, `env`, `credentials`
5. Build the Skyflow client:
   ```python
   skyflow_client = (
       Skyflow.builder()
       .add_vault_config(vault_config)
       .set_log_level(LogLevel.INFO)
       .build()
   )
   ```
6. Request object — plain constructor with keyword arguments (no builder, no separate Options class):
   ```python
   request = InsertRequest(
       table='table_name',
       values=[{'field': 'value'}],
       return_tokens=True,
   )
   ```
7. Call the vault/detect/connection method inside `try/except SkyflowError`:
   ```python
   response = skyflow_client.vault('<VAULT_ID>').insert(request)
   print(response)
   ```
8. Catch `SkyflowError` and print structured error details:
   ```python
   except SkyflowError as e:
       print({'code': e.http_code, 'message': e.message, 'details': e.details})
   ```

## Rules

- Vault IDs / cluster IDs use placeholders: `'<YOUR_VAULT_ID>'`, `'<YOUR_CLUSTER_ID>'`
- Credential values use placeholders: `'<YOUR_API_KEY>'`, `'<YOUR_CREDENTIALS_STRING>'`
- Credentials file path: `'credentials.json'` (relative — no absolute paths)
- Always use single quotes for string literals (matches project style)
- No separate `*Options` classes — they don't exist in this SDK; all options are fields on the request object
- Always catch `SkyflowError` and print `e.http_code`, `e.message`, `e.details`
- Keep under 80 lines
- Do not import from `skyflow.generated.*`

## After creating the file

Verify the file has no syntax errors and that all imports resolve:
```bash
python -m py_compile samples/<directory>/<file>.py && echo "OK"
```

Report the file path and any errors.
