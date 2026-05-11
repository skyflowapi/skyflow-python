---
description: Generate a new Skyflow Python SDK sample file demonstrating a specific feature with proper patterns, error handling, and idiomatic style.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Samples must import only from the public 'skyflow' package, never directly from skyflow/generated/."
---

Create a new Skyflow Python SDK sample. Feature to demonstrate: $ARGUMENTS

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. Samples must import only from the public `skyflow` package, never directly from `skyflow/generated/`.

Read the following before writing anything:
1. An existing sample in `samples/vault_api/` that is closest to the requested feature, to understand structure and style
2. `skyflow/__init__.py` to see what is exported from the top-level package
3. The relevant request class in `skyflow/vault/data/`, `skyflow/vault/tokens/`, `skyflow/vault/detect/`, or `skyflow/service_account/` to understand the constructor signature

---

## Sample requirements

### File location
- Vault CRUD operations → `samples/vault_api/<feature_name>.py`
- Token operations (tokenize, detokenize) → `samples/vault_api/<feature_name>_records.py`
- Connection operations → `samples/vault_api/invoke_connection.py` (extend existing)
- Service account / auth → `samples/service_account/<feature_name>_example.py`
- Detect / PII operations → `samples/detect_api/<feature_name>.py`

### Required structure (in this order)
1. **Import block** — only from the public `skyflow` package; never from `skyflow.generated`
2. **Module-level docstring** — triple-quoted, listing what the sample demonstrates (numbered list)
3. **`cred` dict** — service account credential fields using their camelCase key names (`clientID`, `clientName`, `tokenURI`, `keyID`, `privateKey`) as placeholder strings
4. **`skyflow_credentials` dict** — wrap `cred` as `{'credentials_string': json.dumps(cred)}`
5. **`credentials` dict** — bearer token credential: `{'token': '<YOUR_TOKEN>'}` (shown as the per-vault override)
6. **`primary_vault_config` dict** — `vault_id`, `cluster_id`, `env: Env.PROD`, `credentials`
7. **`skyflow_client`** built with the fluent builder pattern: `.builder().add_vault_config(...).add_skyflow_credentials(...).set_log_level(LogLevel.ERROR).build()`
8. **Request object** constructed using the appropriate `XxxRequest` class with keyword arguments
9. **SDK call** through `skyflow_client.vault(vault_id).operation(request)`
10. **`print()` on success** — print the response object
11. **`except SkyflowError`** block with `http_code`, `message`, `details`
12. **`except Exception`** block for unexpected errors
13. **Top-level call** to the `perform_xxx()` function at the bottom of the file

### Code style rules
- Function name: `perform_<feature_name>()` (snake_case, descriptive of the operation)
- Placeholder values: `'<YOUR_VAULT_ID>'`, `'<YOUR_CLUSTER_ID>'`, `'<TABLE_NAME>'`, `'<COLUMN_NAME>'`, `'<YOUR_TOKEN>'`, etc.
- Step comments: number each logical phase as `# Step 1: Configure Credentials`, `# Step 2: Configure Vault`, `# Step 3: Configure & Initialize Skyflow Client`, `# Step 4: Prepare <Feature> Data`, `# Step 5: Perform <Feature>`
- Every non-obvious argument gets a short inline comment explaining WHY (not what): e.g. `return_tokens=True  # Get tokens for inserted data`
- Keep the sample under 100 lines — if more is needed, split into focused examples
- No `print()` on success other than printing the response
- No hardcoded real credentials, private keys, or tokens — use `'<PLACEHOLDER>'` strings throughout

### Template
```python
import json
from skyflow.error import SkyflowError
from skyflow import Env
from skyflow import Skyflow, LogLevel
from skyflow.vault.data import XxxRequest  # replace with actual import(s)

"""
 * Skyflow <Feature> Example
 *
 * This example demonstrates how to:
 * 1. Configure Skyflow client credentials
 * 2. Set up vault configuration
 * 3. Create a <feature> request
 * 4. Handle response and errors
"""

def perform_<feature_name>():
    try:
        # Step 1: Configure Credentials
        cred = {
            'clientID': '<YOUR_CLIENT_ID>',        # Client identifier
            'clientName': '<YOUR_CLIENT_NAME>',    # Client name
            'tokenURI': '<YOUR_TOKEN_URI>',        # Token URI
            'keyID': '<YOUR_KEY_ID>',              # Key identifier
            'privateKey': '<YOUR_PRIVATE_KEY>',    # Private key for authentication
        }

        skyflow_credentials = {
            'credentials_string': json.dumps(cred)  # Service account credentials
        }

        credentials = {
            'token': '<YOUR_TOKEN>'  # Bearer token for this vault
        }

        # Step 2: Configure Vault
        primary_vault_config = {
            'vault_id': '<YOUR_VAULT_ID>',      # Primary vault
            'cluster_id': '<YOUR_CLUSTER_ID>',  # Cluster ID from your vault URL
            'env': Env.PROD,                    # Deployment environment (PROD by default)
            'credentials': credentials          # Per-vault authentication method
        }

        # Step 3: Configure & Initialize Skyflow Client
        skyflow_client = (
            Skyflow.builder()
            .add_vault_config(primary_vault_config)
            .add_skyflow_credentials(skyflow_credentials)  # Fallback if no vault-level credentials
            .set_log_level(LogLevel.ERROR)                 # Logging verbosity
            .build()
        )

        # Step 4: Prepare <Feature> Data
        # ... build request object ...
        request = XxxRequest(
            # keyword arguments here
        )

        # Step 5: Perform <Feature>
        response = skyflow_client.vault(primary_vault_config.get('vault_id')).<operation>(request)

        # Handle Successful Response
        print('<Feature> successful: ', response)

    except SkyflowError as error:
        print('Skyflow Specific Error: ', {
            'code': error.http_code,
            'message': error.message,
            'details': error.details
        })
    except Exception as error:
        print('Unexpected Error:', error)


# Invoke the function
perform_<feature_name>()
```

### Service account samples (auth only)
For `samples/service_account/` samples that do not use the vault client, omit the `Skyflow` builder block and instead import directly from `skyflow.service_account`. Use a `global bearer_token = ''` pattern with an `is_expired()` guard before calling `generate_bearer_token()` or `generate_bearer_token_from_creds()`. Use `file_path = '<CREDENTIALS_FILE_PATH>'` as the placeholder.

### Detect API samples
For `samples/detect_api/` samples, import request classes from `skyflow.vault.detect`. The client accessor is `skyflow_client.vault(vault_id).detect()` or the detect controller method directly. Follow the same five-step structure.

---

After creating the file:
1. Run the sample with a dry-run import check to verify there are no import errors:
   ```
   python -c "import ast; ast.parse(open('samples/<path>/<file>.py').read()); print('Syntax OK')"
   ```
2. Report the file path created and any import or syntax issues to fix
