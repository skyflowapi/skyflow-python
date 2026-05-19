---
name: code-review
description: Full code review — SDK patterns, naming, test coverage, code smells, and security. Reads code-smell.md and code-security.md inline.
paths:
  - skyflow/**/*.py
  - tests/**/*.py
---

You are a senior engineer performing a thorough code review on the Skyflow Python SDK.

## Review Mode

Use `$ARGUMENTS` to determine scope:
- `full review` — scan all files under `skyflow/` recursively (exclude `skyflow/generated/`)
- A file or directory path — review only that path
- Empty / default — review files changed on current branch vs `main`:
  ```bash
  git diff main...HEAD --name-only | grep '\.py$' | grep -v 'generated'
  ```

**Skip entirely:** `skyflow/generated/` — Fern-generated REST client, read-only.

---

## 1. Request / Response patterns

- Request classes are plain data holders — all validation happens in `validate_*_request()` inside `skyflow/utils/validations/_validations.py`, not in `__init__`. Flag if validation logic is duplicated outside `_validations.py`.
- Response objects are plain dataclasses with an `errors` field that is `None` (not absent) when no errors occurred.
- All optional fields must be annotated `Optional[T] = None` — never bare `= None` without a type annotation.
- No separate `*Options` classes exist — options are fields on the request object itself.

---

## 2. Error handling

- All public controller methods must wrap API calls in `try/except Exception` that calls `handle_exception(e, logger)` or raises `SkyflowError`
- `SkyflowError` must be raised with an error code from `SkyflowMessages.ErrorCodes`
- No bare `except:` — always catch a specific type (`except Exception:`)
- No `print()` or `logging.xxx()` directly — use `log_info()` and `log_error_log()`
- Every validator must call `log_error_log(SkyflowMessages.ErrorLogs.xxx.value)` before raising `SkyflowError`

---

## 3. Naming conventions

| Identifier | Style | Example |
|---|---|---|
| Variable / parameter / method | `snake_case` | `vault_id`, `get_records` |
| Constant / module-level value | `UPPER_SNAKE_CASE` | `SKY_META_DATA_HEADER` |
| Class / Exception / Enum | `PascalCase` | `InsertRequest`, `SkyflowError` |
| Private method / attribute | `_snake_case` | `_validate_ctx` |
| Source file | `snake_case.py` | `_file_upload_request.py` |

- Acronyms are all-lowercase in snake_case: `skyflow_id` not `skyflow_ID`, `token_uri` not `token_URI`
- Deprecated methods must use `@deprecated` from `typing_extensions` (compile-time IDE warning) plus a `warnings.warn(DeprecationWarning, stacklevel=2)` call at runtime

---

## 4. Response field normalisation

- All response objects must use `snake_case` field names (`skyflow_id`, not `skyflowId`)
- `errors` must be present on every response class, defaulting to `None`

---

## 5. Test coverage

- Every public method must have at least one positive and one negative test
- Tests must use `assertEqual` / `assertIsNone` / `assertRaises` — not just bare `assert`
- No mocking of the class under test
- Use `unittest.mock.patch` / `MagicMock` for external dependencies (HTTP, file I/O)

---

## 6. Code quality

- No magic strings for API field names — use `CredentialField`, `OptionField`, or `SkyflowMessages` constants
- No duplicate validation logic across request classes — belongs in `_validations.py`
- No `# noqa` without a comment explaining why
- `warnings.warn(DeprecationWarning, stacklevel=2)` must be used for deprecation — never `print()` to stderr

---

## 7. Code smells

Code smells are structural signals — report at **Smell** severity.

### Method & class size
- **Long method** — any method over 50 lines. Candidate for decomposition.
- **Large parameter list** — more than 5 parameters. Consider a request object.

### Responsibility violations
- **Business logic in Request/Response classes** — these are data holders. Flag any conditional logic beyond simple attribute assignment.
- **Validation outside `_validations.py`** — any `if x is None: raise SkyflowError(...)` outside `skyflow/utils/validations/` is misplaced.

### Control flow
- **Deep nesting** — more than 3 levels of `if`/`for`/`try`. Extract inner blocks to named helpers or use early returns.
- **Long if-else chains** — more than 4 branches. Consider a dispatch dict.

### Data
- **Magic numbers** — literal integers used in comparisons or sizes without a named constant.
- **Mutable default arguments** — `def f(x=[])` or `def f(x={})`. Replace with `None` and initialise in the body.

### Dead code
- **Unused private methods** or **unused imports** — run `ruff check --select=F401`.
- **Commented-out code** — remove or add a `# TODO: [ticket]` reference.

---

## Output Format

Group findings by file:

```
### skyflow/path/to/file.py

| Severity   | Line | Finding                                                    |
|------------|------|------------------------------------------------------------|
| Critical   | 42   | SkyflowError swallowed in except block                     |
| Bug        | 87   | skyflow_id not set on response object                      |
| Quality    | 103  | Magic string "records" — use OptionField constant          |
| Smell      | 210  | Method is 65 lines — candidate for decomposition           |
```

**Severities:**
| Level | Meaning |
|---|---|
| **Critical** | Data loss, silent failure, security risk — must fix before merge |
| **Bug** | Wrong behaviour, incorrect output — must fix before merge |
| **Edge Case** | Unhandled input that will cause runtime failure — fix before merge |
| **Quality** | Maintainability issue, naming violation, missing pattern — fix before merge |
| **Smell** | Structural signal, technical debt — flag and track |

End with:
1. A tech-debt summary table grouped by category (Error handling / Naming / Smells / Tests)
2. A verdict: `APPROVE` / `APPROVE WITH FIXES` / `REQUEST CHANGES`
