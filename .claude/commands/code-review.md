---
description: Smart code review for the Skyflow Python SDK. Pass "full review" to scan the entire skyflow/ tree, a file/directory path to review that target, or nothing to review files changed on the current branch.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Filter it out at the git diff step with: git diff --name-only | grep -v 'generated'. If a finding relates to generated code, report it as an observation only."
---

You are a senior engineer reviewing the Skyflow Python SDK — a Python client library for Skyflow's data privacy vault.

## Mode selection — pick exactly one

Inspect `$ARGUMENTS` and choose the review mode:

| Argument | Mode |
|---|---|
| `full review` (case-insensitive) | **Full** — scan all files under `skyflow/` recursively |
| A file or directory path (starts with `/`, `./`, `skyflow/`, `tests/`, `samples/`, etc.) | **Path** — review only that file or directory |
| Empty / anything else | **Branch** — review files changed on the current branch vs `main` |

### Full mode
Scan all files under `skyflow/` recursively, grouped by layer:
```
skyflow/vault/controller/
skyflow/vault/data/
skyflow/vault/tokens/
skyflow/vault/detect/
skyflow/vault/connection/
skyflow/vault/client/
skyflow/utils/validations/
skyflow/utils/
skyflow/service_account/
skyflow/client/
skyflow/error/
skyflow/__init__.py
```
Read each file fully before reporting findings. Work layer by layer — controllers first, then validators, then data models, then utilities.

### Path mode
Restrict the scan to the path given in `$ARGUMENTS` (file or directory). Read every file under that path before reporting.

### Branch mode
Review all files changed on the current branch vs main:
```
git diff main...HEAD --name-only | grep -v 'generated'
git diff main...HEAD
git log main...HEAD --oneline
```
Summarise what the branch does in 2–3 sentences. List files grouped by layer: data models / controllers / validation / service_account / tests / samples / exports / docs.

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. If a finding relates to generated code, report it as an observation only — do not edit, create, or delete any file under that path.

---

## What to review

### Basic checks
- Identify issues and unhandled edge cases that can break the code at runtime.

### 1. Request / Response pattern
- Every public operation must use dedicated classes: `XxxRequest`, `XxxResponse`
- Request classes must declare all fields with explicit types (use `Optional[T]` for optional fields, never bare `None` as the sole annotation)
- Response objects must be plain data containers — no business logic, no API calls inside them
- Flag any controller method that accepts or returns plain `dict` instead of a typed class
- Mutable default arguments in `__init__` are a Python footgun — `def __init__(self, items=[])` mutates the class-level list across instances; use `None` and assign in the body instead

### 2. Validation completeness
- Every public controller method must call its `validate_xxx_request()` function from `skyflow/utils/validations/_validations.py` **before** any API call
- Validators must raise `SkyflowError` with an error code from `SkyflowMessages.ErrorCodes`
- Validators must call `log_error_log(SkyflowMessages.ErrorLogs.xxx.value)` before raising
- Check for missing edge cases: `None` inputs, empty strings, wrong types, empty lists, negative numbers
- No truthy guard `if not x:` for values where `0`, `""`, `False`, or `[]` could be intentionally valid — use `x is None` or `x is not None` instead
- Consistent null-guard style across validators in the changed files — no mixing of `if not x`, `if x is None`, `if x == None`

### 3. Error handling
- All methods that call the REST API must be wrapped in `try/except Exception` that calls `handle_exception(e, logger)` or raises `SkyflowError`
- Never swallow errors silently with a bare `except: pass`
- `except` blocks that re-raise must add value (logging, wrapping) — a bare `except Exception as e: raise e` with no added context should be flagged
- `SkyflowError` must be raised with the correct error code for the failure type (INVALID_INPUT for validation, server codes for API failures)
- Bare `except:` (catching `BaseException`) must be replaced with `except Exception:`

### 4. Concurrency and I/O patterns
- File reads must use context managers (`with open(...) as f:`) — never leave file handles open
- `open()` for binary content must use mode `"rb"` not `"r"`
- Blocking I/O (file reads, network calls) inside a loop must be flagged if the loop runs at high volume — suggest batching
- No module-level side effects that execute on import (network calls, file I/O, env reads at import time)

### 5. Python quality
- No mutable default arguments: `def f(x=[])`, `def f(x={})` — use `None` and initialise in the body
- No `from module import *` in non-`__init__.py` files
- No bare `except:` — always catch a specific exception type
- No `global` or `nonlocal` in controller / validator code
- `isinstance()` checks must cover all relevant types — flag `isinstance(x, int)` where `bool` is a subclass of `int` and would be silently accepted when it should not be, or vice versa
- f-strings preferred over `%` formatting and `.format()` for new code; flag inconsistency within the same file
- `Optional[T]` must be imported from `typing` — do not use `T | None` union syntax unless the minimum Python version is ≥ 3.10

### 6. State and side effects
- Controller instances must be stateless per-call — no `self.xxx = <per-call value>` inside method bodies; use local variables instead
- Cached/memoized state (e.g. `_cached_headers`) must not mix per-call and cross-call data
- Class-level variables shared across instances are a source of subtle bugs — flag any mutable class-level variable

### 7. Exports and public API surface
- All public types and classes must be exported from the appropriate `__init__.py`
- Internal helpers (prefixed with `_`) must not appear in `__init__.py` exports
- Circular imports must not exist — flag any `from skyflow.x import y` inside `skyflow/y/__init__.py` that creates a cycle

### 8. Logging
- Use `log_info(message, logger)` for informational messages and `log_error_log(message, logger)` for errors — never `print()` or `logging.xxx()` directly
- Sensitive values (tokens, credentials, private keys, PII) must never appear in log messages or error strings
- Every public method entry and success path must have a corresponding `log_info` call matching the `SkyflowMessages.Info` enum

### 9. Naming conventions (Python)

| Identifier type | Required style | Example |
|---|---|---|
| Variable / parameter / method | `snake_case` | `vault_id`, `token_uri`, `get_records` |
| Constant / module-level value | `UPPER_SNAKE_CASE` | `SKY_META_DATA_HEADER`, `CTX_KEY_REGEX` |
| Class / Exception / Enum | `PascalCase` | `InsertRequest`, `SkyflowError`, `RedactionType` |
| Private method / attribute | `_snake_case` | `_validate_ctx`, `_cached_headers` |
| Source file | `snake_case.py` or `_snake_case.py` for internals | `_file_upload_request.py`, `_validations.py` |

**Acronym rule — all-lowercase in identifiers, not ALL-CAPS:**
- `id` not `ID` (e.g. `skyflow_id`, not `skyflow_ID`)
- `uri` not `URI` (e.g. `token_uri`, not `token_URI`)
- `url` not `URL` (e.g. `callback_url`, not `callback_URL`)
- `api` not `API` (e.g. `api_key`, not `API_key`)
- Exception: class names follow PascalCase title-casing: `SkyflowId`, `TokenUri`; standalone environment variable names follow OS convention (`SKYFLOW_ID`, `TOKEN_URI`)

**What to flag:**
- Any public field, method, or parameter name that uses ALL-CAPS for an acronym in a snake_case context
- Any `camelCase` field or method name in the public API
- Any class, exception, or enum name that is not `PascalCase`
- Any constant that is not `UPPER_SNAKE_CASE`
- Mixed conventions within the same class or module

### 10. Type annotations
- All public method signatures must have parameter type annotations and a return type annotation
- `Any` usage outside `skyflow/generated/` must be justified — flag unannotated parameters that default to implicit `Any`
- `dict` without subscript (`dict` not `dict[str, Any]`) in a public signature must be flagged
- `Optional[T]` parameters must default to `None` — `def f(x: Optional[str])` without `= None` is a bug

### 11. Function size and complexity
- Flag any function exceeding 50 lines — include the actual line count
- Flag nesting deeper than 3 levels — suggest early returns or extracted helpers
- Flag long `if valid: … entire body …` blocks where an inverted guard + early return would flatten the code
- Flag validator functions that duplicate logic already present in another validator — suggest extracting a shared helper

### 12. Cross-cutting consistency
- All `XxxRequest` classes must declare optional fields with `Optional[T] = None`, not bare `= None`
- All validators must call `log_error_log` before raising `SkyflowError` — flag any that raise directly without logging
- Controller methods must use a consistent call style — flag mixing of direct API calls and `.with_raw_response` within the same controller
- Credential field access must use `CredentialField` constants, not hardcoded strings like `"clientID"` or `"tokenURI"`

---

## Output format

Group findings by file. For each issue:

```
[SEVERITY] file:line — Description
  Problem: <what is wrong>
  Fix: <concrete suggestion>
```

Severity levels: **CRITICAL** | **BUG** | **EDGE CASE** | **QUALITY**

End with:

**Summary table**
| Severity | Count |
|---|---|
| CRITICAL | n |
| BUG | n |
| EDGE CASE | n |
| QUALITY | n |
| **Total** | n |

**Top 5 highest-priority fixes** (by risk, not count)

**Verdict**: `APPROVE` | `APPROVE WITH FIXES` | `REQUEST CHANGES`
One sentence explaining the verdict.
