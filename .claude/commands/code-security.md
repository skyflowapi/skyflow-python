---
name: code-security
description: Security audit — credential exposure, input validation, path traversal, HTTP security, token lifecycle, dependency CVEs.
paths:
  - skyflow/service_account/**/*.py
  - skyflow/vault/client/**/*.py
  - skyflow/vault/controller/**/*.py
  - skyflow/utils/**/*.py
  - requirements.txt
---

You are a security engineer auditing the Skyflow Python SDK for vulnerabilities.

## Audit Scope

Use `$ARGUMENTS` to determine target files. If none provided, run:
```bash
git diff main...HEAD --name-only | grep '\.py$' | grep -v 'generated'
```

**Skip:** `skyflow/generated/` — observations only, no edits.

## Security Checks

### 1. Credential and token exposure (Critical)
- Bearer tokens, API keys, and private keys must never appear in log messages (`log_info`, `log_error_log`), `SkyflowError` message strings, or `__repr__` / `__str__` output
- `CredentialField` values (`private_key`, `client_id`, `token_uri`) must not be serialised to logs
- JWT claims must not be logged
- `except` blocks must not log `str(e)` or `repr(e)` when the exception may contain auth headers or credential fields

### 2. Input validation (High)
- All user-supplied strings passed to `open()`, `os.path.exists()`, or `os.path.join()` must be validated for path traversal (`../`, `..\\`, null bytes `\x00`)
- Regex patterns from user input must be compiled inside `try/except re.error` to prevent `re.error` or ReDoS
- `base64.b64decode()` on external data must use `validate=True` and have a size check before decoding

### 3. File handling (High)
- All `open()` calls must use a context manager (`with open(...) as f:`) — bare `open()` leaks handles on exception paths
- User-supplied directory paths must be validated with `os.path.isdir()` before use — never call `os.makedirs()` on arbitrary user input
- Output file paths must be constructed with `os.path.join(validated_base, sanitised_name)` — never string concatenation with unsanitised components
- Temporary files must use `tempfile.NamedTemporaryFile` or `tempfile.mkstemp()`, never `"/tmp/" + user_value`

### 4. HTTP security (Medium)
- All API calls must use HTTPS — flag any hardcoded `http://` URL or URL assembled without a scheme check
- SSL verification must never be disabled (`verify=False` in `httpx` or `requests` calls)
- Auth headers (`Authorization`, `X-Skyflow-Authorization`) must not be logged at any level
- HTTP clients must be configured with connection and read timeouts — flag absent `timeout=` parameters

### 5. Error information leakage (Medium)
- `SkyflowError` messages must not include raw server response bodies, internal file system paths, or Python tracebacks
- `handle_exception()` must strip sensitive server details before wrapping in `SkyflowError`
- `except` blocks must log only controlled message strings from `SkyflowMessages.ErrorLogs` — never `str(e)` from exceptions that may contain credentials

### 6. Dependency vulnerabilities (Low)
- Run `pip-audit` against `requirements.txt` and report HIGH / CRITICAL CVEs:
  ```bash
  pip install pip-audit && pip-audit -r requirements.txt
  ```
- Flag unpinned dependencies on security-sensitive packages (`cryptography`, `PyJWT`, `httpx`, `requests`) — prefer `~=` or exact pins over open `>=`

### 7. Authentication lifecycle (Medium)
- Bearer tokens fetched via `generate_bearer_token()` must be checked with `is_expired()` immediately before each API call
- `is_expired()` must decode without signature verification only for expiry checking — it must not bypass actual auth decisions
- JWT signing must use `RS256` — flag any path where the algorithm could be set to `HS256` with a user-supplied secret
- Service account credentials files must not be world-readable — check `os.stat(path).st_mode` for `0o644`

## Output Format

For each finding:

```
### skyflow/path/to/file.py : line N

**Severity:** Critical / High / Medium / Low / Info
**Risk:** What an attacker or misconfiguration could cause
**Trigger:** Input or code path that triggers the vulnerability
**Fix:** Concrete remediation
**CWE:** CWE-NNN
```

End with a summary table and overall risk rating (Critical / High / Medium / Low).
