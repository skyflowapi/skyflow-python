---
description: Security audit for the Skyflow Python SDK — credentials, injection, file I/O, deps, auth lifecycle, HTTP safety.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Filter it out at the git diff step with: git diff --name-only | grep -v 'generated'. If a finding relates to generated code, report it as an observation only."
---

You are a security engineer auditing the Skyflow Python SDK — a Python library that handles sensitive PII and credentials. Perform a security review on the target: $ARGUMENTS

If no argument is given, scan all files changed on the current branch vs main:
```
git diff main...HEAD --name-only | grep -v 'generated'
```

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. If a security finding relates to generated code, report it as an observation only — do not edit, create, or delete any file under that path.

Read each target file fully before reporting findings. For any file that touches authentication, file I/O, or HTTP calls, also read the related controller and validation file.

---

## Security checks

### 1. Credential and token exposure
- Bearer tokens, API keys, private keys, and service account credentials must **never** appear in:
  - Log messages at any level (`log_info`, `log_error_log`, or any `print()`)
  - `SkyflowError` message strings or detail fields
  - Response objects returned to callers
  - File names or paths written to disk
- Check that bearer tokens returned by `generate_bearer_token()` / `get_service_account_token()` are not stored as instance attributes on controllers or at module level — tokens must be used immediately or cached only with a validated expiry check
- Verify that credentials passed in `credentials` dicts or `CredentialField` values are not echoed back in any response, log entry, or raised exception
- Check that `except` blocks do not accidentally log the full exception object (`str(e)`, `repr(e)`) when the exception may contain auth headers or credential fields
- Private keys read from disk or passed as strings must be zero-reference after use — check they are not bound to a long-lived variable on `self`

### 2. Input validation and injection
- All user-supplied strings passed to file system APIs (`open()`, `os.path.exists()`, `os.path.isfile()`, `os.makedirs()`, `shutil.*`) must be validated before use:
  - Path traversal: reject strings containing `../`, `..\\`, or null bytes (`\x00`)
  - Absolute paths escaping an expected base directory — verify with `os.path.realpath()` and confirm the result is still under the expected root
- Regex patterns supplied by users (e.g. `allow_regex_list`, `restrict_regex_list` in detect/deidentify requests) must be compiled inside a `try/except re.error` block before use — a malformed or catastrophic pattern causes `re.error` or ReDoS
- `base64.b64decode()` on data from API responses or user input must have a size check before decoding — an unbounded payload can cause OOM; also call with `validate=True` to reject non-base64 characters
- Ensure no user-controlled string reaches `eval()`, `exec()`, `subprocess.run/Popen` with `shell=True`, `os.system()`, or `__import__()`
- `pickle.loads()` / `pickle.load()` must never be called on data from external sources (API responses, user files, environment variables) — pickle is an arbitrary code execution vector
- `yaml.load()` must always specify `Loader=yaml.SafeLoader` — bare `yaml.load()` executes arbitrary Python
- SQL-like query strings passed to the vault API (`QueryRequest`) must be treated as opaque — verify no string interpolation of user data occurs before the SDK forwards the query to the API

### 3. File system security
- User-supplied directory paths (e.g. `output_directory` in deidentify file requests) must be validated to be an existing, accessible directory using `os.path.isdir()` — the SDK must not call `os.makedirs()` on arbitrary user-supplied paths
- Output file paths must be constructed with `os.path.join(validated_base_dir, sanitized_file_name)` — never raw string concatenation or f-strings with unsanitized components
- File name components that come from API responses (extensions, type names, `processed_file_extension`) must be sanitized before use in a path — they could contain `../`, leading dots, or special characters if the response is tampered with
- File handles must always be closed via `with open(...) as f:` — bare `open()` without a context manager leaks handles on exception paths
- Temporary files must use `tempfile.NamedTemporaryFile` or `tempfile.mkstemp()`, never manually constructed paths like `"/tmp/" + user_value`
- Temporary or intermediate files written during processing must be cleaned up on both success and error paths (use `try/finally`)

### 4. Dependency and supply chain
- Run `pip-audit` (or `safety check`) and report all HIGH and CRITICAL severity findings with CVE IDs:
  ```
  pip install pip-audit && pip-audit -r requirements.txt
  ```
- Check `requirements.txt` for unpinned dependencies — floating `>=` without an upper bound on security-sensitive packages (`cryptography`, `PyJWT`, `requests`, `httpx`, `urllib3`) is risky; prefer `~=` (compatible release) or exact pins
- Flag any `importlib.import_module()` or `__import__()` call where the module name is derived from user input or environment variables
- Check that `cryptography` and `PyJWT` are recent enough to avoid known CVEs (check pinned versions against current release)

### 5. Error message information leakage
- `SkyflowError` messages surfaced to callers must not include: internal file system paths, raw Python tracebacks (`traceback.format_exc()`), server-side query details, or internal service hostnames
- `except` blocks that call `log_error_log` must log only a controlled message string from `SkyflowMessages.ErrorLogs` — never `str(e)` or `repr(e)` from an exception that may contain credentials or server internals
- HTTP response bodies from API errors must be stripped of internal server details (stack traces, internal hostnames, database names) before being wrapped in `SkyflowError`
- Ensure `SkyflowError` fields (`message`, `http_code`, `grpc_code`) contain only information safe to surface to SDK consumers — no raw server error objects

### 6. Authentication and token lifecycle
- Bearer tokens fetched via `generate_bearer_token()` must be checked with `is_expired()` immediately before the API call — the token could expire between retrieval and use (TOCTOU)
- `is_expired()` must decode without signature verification (`verify_signature: False`) only for expiry checking — it must not be used to bypass signature verification for actual authentication decisions
- JWT signing in `get_signed_jwt()` must use `RS256` or `ES256` — flag any path where `algorithm` could be set to `HS256` with a user-supplied or weak secret
- API key validation must check both the `sky-` prefix and the exact length (42 characters per `ApiKey.LENGTH`) — a check on only one criterion is insufficient
- Check that no credential type silently falls through to a less-secure fallback (e.g. ignoring an invalid token and falling back to no auth) without raising or logging a warning
- Service account credentials read from disk must validate that the file is not world-readable (`os.stat(path).st_mode`) — a credentials file with mode `0o644` is readable by all local users

### 7. HTTP and network security
- All HTTP calls made through `httpx` or `requests` must use HTTPS — flag any hardcoded `http://` URL or any URL assembled from user-supplied components without a scheme check
- SSL verification must never be disabled: `verify=False` in `httpx.Client()` or `requests.get(..., verify=False)` bypasses certificate validation and enables MITM attacks
- Auth headers (`Authorization`, `X-Skyflow-Authorization`) must not be logged, echoed in error messages, or forwarded to redirect targets
- `x-request-id` and other response headers must be read only — verify they are never interpolated into subsequent outgoing requests (header injection)
- HTTP clients must be configured with connection and read timeouts — an absent timeout means a hung server stalls the calling thread indefinitely; check for `timeout=` parameters on all `httpx` / `requests` calls
- Check that the SDK does not silently retry on `401 Unauthorized` without first refreshing the token — silent retry with a stale token masks credential rotation failures

### 8. Secrets in source and configuration
- Check all files for accidentally committed secrets: JWT private keys, API keys matching `sky-[A-Za-z0-9]{38}`, PEM blocks (`-----BEGIN RSA PRIVATE KEY-----`), or base64 blobs > 200 chars in non-test files
- `.env` files and `credentials.json` must be listed in `.gitignore` — verify they are not tracked
- Test fixture files (`tests/`) must use obviously fake credentials (e.g. dummy PEM blocks, placeholder strings) — real-looking keys in tests are a supply-chain risk if the repo becomes public
- Environment variable reads (`os.environ.get(...)`) for credential material must have a documented fallback policy — silently returning `None` and continuing is an authentication bypass

### 9. Generated code (`skyflow/generated/`)
- Do not modify — but verify it uses HTTPS only, applies auth headers from the SDK layer, and does not hardcode environment-specific endpoints
- Flag if the generated client disables SSL verification or sets a permissive timeout of `None`
- Flag if the generated client silently retries on auth failure without surfacing the error to the caller

---

## Output format

For each finding:

```
[SEVERITY] file:line — Finding title
  Risk: <what an attacker or misconfiguration could cause>
  Trigger: <how to reach this code path>
  Fix: <concrete remediation>
  CWE: <CWE-ID if applicable>
```

Severity: **CRITICAL** | **HIGH** | **MEDIUM** | **LOW** | **INFO**

End with:
1. Overall risk rating (Critical / High / Medium / Low)
2. Top 3 highest-priority fixes
3. Whether the code is safe to ship as-is
