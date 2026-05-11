---
name: pr-review
description: Full pull-request review for the Skyflow Python SDK. Covers code quality, SDK patterns, tests, docs, security, breaking-change detection, naming conventions, edge cases, and coverage.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Filter it out at the git diff step with: git diff --name-only | grep -v 'generated'. If a finding relates to generated code, report it as an observation only."
---

You are a senior engineer conducting a pull-request review for the Skyflow Python SDK — a Python client library for Skyflow's data privacy vault.

Review the target PR or branch: $ARGUMENTS

If no argument is given, diff the current branch against main:
```
git diff main...HEAD
git diff main...HEAD --name-only
git log main...HEAD --oneline
```

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. If a finding relates to generated code, report it as an observation only — do not edit, create, or delete any file under that path.

---

## Step 1 — Understand the change

- Summarise what the PR does in 2–3 sentences.
- List every file changed, grouped by layer: data model / controller / validation / service_account / tests / samples / exports / docs.
- Identify the primary change type: **new feature** | **bug fix** | **refactor** | **docs** | **dependency update**.

---

## Step 2 — Breaking-change detection

- [ ] No public class or method removed from `skyflow/__init__.py`
- [ ] No public method signature changed (parameter added/removed/reordered, type narrowed, default removed)
- [ ] No `XxxRequest` / `XxxResponse` field renamed or removed
- [ ] No error code value changed (string identity in `SkyflowMessages.Error` or `SkyflowMessages.ErrorCodes`)
- [ ] No `LogLevel` or `Env` enum value changed
- [ ] No `CredentialField` or `RedactionType` enum value changed
- [ ] If a breaking change exists: is it intentional and documented in `CHANGELOG.md`?

Flag any breaking change as **BREAKING** even if intentional.

---

## Step 3 — SDK pattern compliance

### Request / Response
- [ ] Every new public operation uses `XxxRequest` and `XxxResponse` dedicated classes
- [ ] Request classes declare all fields with explicit `Optional[T] = None` for optional fields — never bare `= None` without a type annotation
- [ ] Required parameters come before optional ones in `__init__` signatures
- [ ] Response objects are plain data containers — no business logic, no API calls inside them
- [ ] No controller method that accepts or returns a plain `dict` instead of a typed class

### Validation
- [ ] Every public controller method calls its `validate_xxx_request()` from `skyflow/utils/validations/_validations.py` **before** any API call
- [ ] Validators raise `SkyflowError` with a code from `SkyflowMessages.ErrorCodes`
- [ ] `log_error_log(SkyflowMessages.ErrorLogs.xxx.value, logger)` called **before** raising — never after
- [ ] Edge cases covered: `None` inputs, empty strings, empty lists, wrong types, negative numbers
- [ ] No truthy guard `if not x:` for values where `0`, `""`, `False`, or `[]` could be valid — use `x is None` instead
- [ ] Consistent null-guard style across all validators in the changed files — no mixing of `if not x`, `if x is None`, `if x == None`

### Error handling
- [ ] All methods calling the REST API are wrapped in `try/except Exception` that calls `handle_exception(e, logger)` or raises `SkyflowError`
- [ ] No silent error swallowing (`except: pass` or `except Exception: pass`)
- [ ] No no-op catch (`except Exception as e: raise e` with no added value — no logging, no wrapping)
- [ ] `SkyflowError` raised with the correct code for the failure type (`INVALID_INPUT` for validation, server codes for API failures)
- [ ] No bare `except:` — always `except Exception:` or a specific exception type

### I/O and resource patterns
- [ ] `open()` always used as a context manager (`with open(...) as f:`) — never left open on exception
- [ ] Binary file reads use mode `"rb"` not `"r"`
- [ ] No module-level side effects that execute on import (network calls, file I/O, env reads at module load time)
- [ ] No blocking I/O or `time.sleep()` in a tight loop without a comment explaining the retry strategy

### Python quality
- [ ] No mutable default arguments: `def f(x=[])`, `def f(x={})` — use `None` and initialise in the body
- [ ] No `from module import *` in non-`__init__.py` files
- [ ] No bare `except:` — always a specific exception type
- [ ] No `global` or `nonlocal` in controller or validator code
- [ ] `isinstance()` preferred over `type(x) == T` — covers subclasses
- [ ] `is None` / `is not None` preferred over `== None` / `!= None`
- [ ] f-strings preferred over `%` formatting and `.format()` for new code; flag inconsistency within the same file
- [ ] `Optional[T]` imported from `typing` — do not use `T | None` union syntax unless minimum Python version is ≥ 3.10

### Function size and complexity
- [ ] No function exceeds 50 lines — flag with actual line count
- [ ] No nesting deeper than 3 levels — suggest early returns or extracted helpers
- [ ] Long `if valid: ...entire body...` blocks replaced with inverted guard + early return
- [ ] No long `try` block spanning more than 10 lines — unclear which statement actually raised; split into one `try/except` per operation

### State / side effects
- [ ] Controller instances are stateless per-call — no `self.xxx = <per-call value>` inside method bodies; use local variables
- [ ] No mutable class-level variables shared across instances
- [ ] Cached state (e.g. `_cached_headers`) does not mix per-call and cross-call data

---

## Step 4 — Exports and public API surface

- [ ] New public types/classes exported from the appropriate `__init__.py`
- [ ] Internal helpers (prefixed `_`) not accidentally exported
- [ ] No circular imports introduced
- [ ] `skyflow/__init__.py` exports updated if new public surface was added

---

## Step 5 — Tests

- [ ] Test file exists at `tests/vault/controller/`, `tests/service_account/`, or `tests/utils/`
- [ ] Happy path covered
- [ ] One test per new error code / validation branch
- [ ] API error response handled
- [ ] Async / polling / retry logic tested if applicable
- [ ] No tests removed without explanation
- [ ] `.venv/bin/python -m pytest tests/ --import-mode=importlib -q` passes with no new failures
- [ ] **100% line coverage** on every new or changed file — flag any uncovered lines
- [ ] **Branch coverage ≥ 80%** on every new or changed file

**Edge case coverage check — for every new/changed source file:**
Read the source and test file together. Flag any of these scenarios that exist in the code but have no test:
- `None` passed to public methods
- Empty string, empty list, zero, negative number inputs
- Wrong type passed where a specific type is expected
- Error paths inside `except` blocks that are never triggered
- Boundary conditions (exactly at a limit vs. one over)
- Credential fields missing, malformed, or using snake_case vs camelCase variants
- Same controller/client reused across two consecutive calls (state leakage)

List each gap as:
```
UNCOVERED EDGE CASE: <file>:<line> — <scenario missing>
```

---

## Step 6 — Sample code

- [ ] Sample exists in `samples/vault_api/`, `samples/detect_api/`, or `samples/service_account/`
- [ ] Imports only from the public `skyflow` package — never from `skyflow.generated`
- [ ] Uses `XxxRequest` classes with keyword arguments
- [ ] Shows `try/except SkyflowError` handling with `http_code`, `message`, `details`
- [ ] Uses the fluent `Skyflow.builder()` pattern
- [ ] No hardcoded real credentials, tokens, or private keys — uses `'<PLACEHOLDER>'` strings
- [ ] Syntax-checks cleanly: `python -c "import ast; ast.parse(open('samples/...').read()); print('Syntax OK')"`

---

## Step 7 — Documentation & logging

- [ ] Docstring on new public-facing classes and methods where the behaviour is non-obvious
- [ ] No `print()` in SDK source — uses `log_info(message, logger)` for info and `log_error_log(message, logger)` for errors
- [ ] Sensitive values (tokens, credentials, private keys, PII) never appear in log messages or error strings
- [ ] Every public method entry and success path has a corresponding `log_info` call matching the `SkyflowMessages.Info` enum
- [ ] `CHANGELOG.md` updated if this is a user-visible change

---

## Step 8 — Security spot-check

- [ ] No credentials or tokens hardcoded or logged
- [ ] No new external HTTP calls outside the generated REST client
- [ ] No `eval()`, `exec()`, `pickle.loads()`, or `yaml.load()` without `Loader=yaml.SafeLoader`
- [ ] No `subprocess` calls with user-controlled input (shell injection risk)
- [ ] No `open()` with a user-supplied path that is not sanitised (path traversal risk)
- [ ] New dependencies in `requirements.txt` or `setup.py` are well-known, maintained packages — flag any unfamiliar ones
- [ ] No `verify=False` in `httpx`/`requests` calls (disables TLS verification)

---

## Step 9 — Naming conventions (Python)

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

- [ ] No ALL-CAPS acronyms in public field, method, parameter, or variable names
- [ ] No `camelCase` fields or methods in the public API (external credential dicts are exempt)
- [ ] All classes, exceptions, and enums are `PascalCase`
- [ ] All module-level constants are `UPPER_SNAKE_CASE`
- [ ] No mixed conventions within the same class or module

---

## Output format

For each issue, output:

```
[SEVERITY] file:line — Short title
  Problem: <what is wrong>
  Fix: <concrete suggestion>
```

Severity levels: **BREAKING** | **CRITICAL** | **BUG** | **EDGE CASE** | **QUALITY** | **NITPICK**

End with:

**Summary table**
| Severity | Count |
|---|---|
| BREAKING | n |
| CRITICAL | n |
| BUG | n |
| EDGE CASE | n |
| QUALITY | n |
| NITPICK | n |
| Uncovered edge cases | n |

**Verdict**: `APPROVE` | `APPROVE WITH FIXES` | `REQUEST CHANGES`
One sentence explaining the verdict.
