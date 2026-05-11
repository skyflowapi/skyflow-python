---
description: Code smell and anti-pattern detection for the Skyflow Python SDK — duplication, dead code, magic values, naming, complexity, Python-specific pitfalls.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Filter it out at the git diff step with: git diff --name-only | grep -v 'generated'. If a smell is found in generated code, report it as an observation only."
---

You are a Python code quality engineer. Identify code smells, anti-patterns, and maintainability issues in the Skyflow Python SDK. Target: $ARGUMENTS

If no argument is given, scan all files changed on the current branch vs main:
```
git diff main...HEAD --name-only | grep -v 'generated'
```

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. If a smell is found in generated code, report it as an observation only — do not edit, create, or delete any file under that path.

Read each target file fully before reporting findings.

---

## Code smell categories

### 1. Python anti-patterns
- **Mutable default arguments** — `def f(self, items=[], config={})` creates a single shared object across all calls; replace with `None` and initialise inside the body (`if items is None: items = []`)
- **Bare `except:`** without an exception type — catches `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, which should never be silently swallowed; replace with `except Exception:`
- **`except Exception: pass`** or **`except Exception: continue`** — silently swallows all errors; at minimum log the exception before swallowing
- **`except Exception as e: raise e`** with no added context — no-op catch that obscures the real traceback; remove it or add logging before re-raising
- **Truthy guard on values where `0`, `""`, `False`, or `[]` are valid** — `if not x:` treats these as falsy when they may be intentional; use `if x is None:` or `if x is not None:`
- **`== None` / `!= None`** — use `is None` / `is not None`; `==` calls `__eq__` and can be overridden by any object
- **`from module import *`** outside `__init__.py` — pollutes the namespace and makes dependency tracking impossible; list explicit names
- **`global` or `nonlocal` inside controller / validator code** — hidden state mutation; use return values or class attributes instead
- **String concatenation in a loop** (`result += s`) — quadratic time; use `"".join(parts)` instead
- **`type(x) == SomeType`** instead of `isinstance(x, SomeType)` — misses subclasses; use `isinstance` unless an exact type check is intentional

### 2. I/O and resource management
- **`open()` without a context manager** — file handle is left open on exception; always use `with open(...) as f:`
- **`open()` for binary content with mode `"r"`** instead of `"rb"` — silently corrupts binary data on Windows and may crash on non-UTF-8 content
- **Blocking I/O inside a hot loop** — file reads, network calls, or `time.sleep()` inside a tight loop without batching; flag any loop that makes one network call per item when a batch API exists
- **No `finally` / context manager for cleanup** — temporary files, open handles, or partially-written outputs not cleaned up on the error path
- **`time.sleep()` in non-test code without a comment** — busy-wait without a timeout ceiling; flag and ask whether exponential backoff or a bounded retry is more appropriate

### 3. Duplication
- Identical or near-identical validation blocks (type check → empty check → element check) copy-pasted across multiple `validate_xxx` functions — extract a reusable `_validate_required_field()` helper
- The same `try: … except: raise SkyflowError(SkyflowMessages.Error.XXX.value, invalid_input_error_code)` wrapper repeated for identical failure modes — consolidate into a shared utility
- `_build_xxx_body()` / `_build_xxx_records()` methods that follow the same structure but differ only by request type — consider a shared builder parameterised by the differing fields
- Log calls (`log_info(SkyflowMessages.Info.XXX_TRIGGERED.value, logger)`) copy-pasted at the start of every controller method with no variation — consider a decorator or base-class hook for entry/exit logging
- Credential field extraction blocks (read `privateKey`, `clientID`, `keyID`, `tokenURI` with individual `try/except` per field) repeated across functions — extract a `_extract_credential_fields(credentials)` helper

### 4. Dead / no-op code
- Variables assigned but never read after assignment
- Imports that are never referenced — run `flake8 --select=F401` or `ruff check --select=F401` to identify
- `if False:` / `if True:` branches — dead by construction
- `return None` at the end of a function that already returns `None` implicitly — redundant
- `# TODO`, `# FIXME`, or `# HACK` comments without a linked ticket — untracked TODOs rot permanently; flag all occurrences
- Code guarded by a Python version check that can never be `False` given the SDK's stated minimum Python version
- `pass` in an `except` block with a comment explaining the exception is expected — convert to `except SpecificError:` with a short inline explanation, or raise if the exception should not be swallowed

### 5. Magic values
- Hardcoded status strings (`"IN_PROGRESS"`, `"SUCCESS"`, `"FAILED"`, `"UNKNOWN"`) in controller logic — use the corresponding enum values from `DetectStatus` or equivalent
- Hardcoded numeric literals for timeouts, retry counts, or max sizes with no named constant — define in `constants.py` with an `UPPER_SNAKE_CASE` name and a comment explaining the constraint
- Hardcoded credential key strings (`"clientID"`, `"tokenURI"`, `"privateKey"`) outside the `_normalize_credentials` mapping — all credential field access must go through `CredentialField` constants
- Hardcoded grant type string `"urn:ietf:params:oauth:grant-type:jwt-bearer"` repeated at multiple call sites — define once in the `JWT` constants class
- Hardcoded algorithm string `"RS256"` outside `JWT.ALGORITHM_RS256` — use the constant everywhere
- Hardcoded integer HTTP codes (200, 400, 500) in business logic — use `HttpStatusCode` constants

### 6. Naming and clarity
- Vague variable names (`data`, `obj`, `temp`, `res`, `req`, `result`) in non-trivial logic — name after the domain concept (`insert_response`, `token_claims`, `credentials_dict`)
- Single-letter loop variables (`i`, `k`, `v`) outside trivial numeric ranges — use descriptive names (`token`, `record`, `vault_id`)
- Method names that imply a return value but only produce a side effect, or vice versa — align name with behaviour
- Typos in public class, method, or constant names — these are breaking changes once shipped; flag immediately

**Python naming conventions — flag any violation:**

| Identifier type | Required style | Example |
|---|---|---|
| Variable / parameter / method | `snake_case` | `vault_id`, `token_uri`, `get_records` |
| Constant / module-level value | `UPPER_SNAKE_CASE` | `SKY_META_DATA_HEADER`, `CTX_KEY_REGEX` |
| Class / Exception / Enum | `PascalCase` | `InsertRequest`, `SkyflowError`, `RedactionType` |
| Private method / attribute | `_snake_case` | `_validate_ctx`, `_cached_headers` |
| Source file | `snake_case.py` or `_snake_case.py` for internals | `_file_upload_request.py` |

**Acronym rule — all-lowercase in snake_case identifiers:**
- `id` not `ID` (e.g. `skyflow_id`, not `skyflow_ID`)
- `uri` not `URI` (e.g. `token_uri`, not `token_URI`)
- `url` not `URL` (e.g. `callback_url`, not `callback_URL`)
- `api` not `API` (e.g. `api_key`, not `API_key`)
- Exception: class names use PascalCase title-casing (`SkyflowId`, `TokenUri`); standalone environment variable names follow OS convention (`SKYFLOW_ID`, `TOKEN_URI`)
- Mixed conventions within the same class or module — flag as inconsistency
- Any `camelCase` field, method, or local variable in SDK source (not in external credential dicts) — belongs in JavaScript/TypeScript, not Python

### 7. Single responsibility
- Controller methods that mix HTTP transport with business logic (polling, file writing, response transformation) — each concern belongs in its own private method
- Validator functions that both validate and transform/normalise data — validation must only raise or pass; normalisation is a separate step (e.g. `_normalize_credentials`)
- Response parsers that also write to the file system — parsing and I/O must be separate functions
- `__init__` methods that perform network I/O or file reads — construction must be side-effect free; defer to an explicit `initialize()` or lazy-init method
- A single `if/elif` chain longer than 5 branches dispatching on a string type — extract a dispatch table (`dict` mapping type → handler) or split into separate methods

### 8. Consistency across the SDK
- Some controller methods call `self.__initialize()` before the API call; others do not — this must be consistent for all public methods that require an initialised client
- Some validators call `log_error_log` before raising `SkyflowError`; others raise directly without logging — every validator must log before it raises
- Credential field access mixes `CredentialField` constants with hardcoded strings — use constants everywhere; mixing makes refactoring dangerous
- Some `XxxRequest` classes use `Optional[T] = None` for optional fields; others use bare `= None` without a type annotation — all optional fields must be annotated `Optional[T] = None`
- Required parameters placed after optional (`= None`) parameters in `__init__` — required parameters must always come first; optional at the end
- `log_info` call style varies (keyword vs positional `logger` argument) — pick one style per function signature and apply consistently
- HTTP response parsing uses `.with_raw_response` in some controllers and not in others — document the reason or standardise

### 9. Validator completeness
- Validators that raise `SkyflowError` without calling `log_error_log(SkyflowMessages.ErrorLogs.xxx.value)` first — without the log there is no trace of the failure in production
- Validators that use `if not x:` instead of `if x is None:` — the truthy check silently rejects `0`, `""`, and `False` as invalid when they may be legitimate values
- Inconsistent null-guard style across validators (`if not x`, `if x is None`, `if x == None`) — pick one style and apply everywhere so edge cases are not missed in some paths but not others
- Validators that check a field's presence but not its type, or its type but not its emptiness — a complete field check is: present → correct type → non-empty / valid value
- Missing conditional validation for optional fields that carry constraints when provided (e.g. a string that must be a valid URL when non-`None`) — the validator must include an `if field is not None:` branch for such fields

### 10. Function size and complexity
- Any function exceeding 50 lines — flag it with its actual line count; a function that long almost always violates single responsibility and is hard to test in isolation
- Nesting deeper than 3 levels (`if` inside `if` inside `for` inside `if`) — deep nesting hides edge cases; extract inner blocks into named helpers or use early returns
- **Missing guard / early return** — when a function opens with a long `if valid: … entire body …` block instead of `if not valid: raise/return`, the happy path is buried; invert the guard and return early
- Long `try` blocks spanning more than 10 lines — it is unclear which statement actually raised; split into one `try/except` per operation
- Chained ternary expressions (`a if cond1 else b if cond2 else c if cond3 else d`) — unreadable beyond two levels; use an explicit `if/elif/else` block

### 11. Type annotation completeness
- Public method signatures missing parameter type annotations or a return type annotation — all public API surface must be fully annotated
- `dict` without subscript (`dict` instead of `dict[str, Any]`) in a public method signature — annotate key and value types explicitly
- `Optional[T]` parameters that do not default to `None` — `def f(x: Optional[str])` without `= None` is misleading and forces callers to pass `None` explicitly
- `Any` usage outside `skyflow/generated/` without a comment explaining why — every `Any` is a type-safety hole; flag all unannotated occurrences
- Inconsistent annotation style: some files use `Optional[T]`, others use `T | None` union syntax — pick one style for the minimum supported Python version and apply it throughout

### 12. Error handling completeness
- `except Exception as e: raise SkyflowError(...)` that does not preserve the original error text — include `str(e)` or chain with `raise SkyflowError(...) from e` so the original context survives into production logs
- `except Exception` that catches a broad class but only handles one specific subtype, silently ignoring all others — add an `else: raise` or handle all expected subtypes explicitly
- Missing `finally` block when a resource (file, network connection, lock) is acquired inside a `try` — a naked `try/except` that does not release on the error path leaks the resource

---

## Output format

Group findings by category. For each smell:

```
[CATEGORY] file:line — Smell name
  Why it's a problem: <1 sentence>
  Suggested fix: <concrete action>
```

End with:
1. Top 5 highest-impact refactors (effort vs. benefit)
2. Estimated tech-debt score per category (High / Medium / Low)
