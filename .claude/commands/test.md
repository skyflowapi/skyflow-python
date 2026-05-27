---
name: test
description: Quality pipeline — lint, spell check, tests, coverage analysis. Pass a test class or module path to target a single test.
paths:
  - skyflow/**/*.py
  - tests/**/*.py
---

Run the Skyflow Python SDK quality pipeline.

Use `$ARGUMENTS` to target a specific test module (e.g. `tests.client.test_skyflow`). If empty, run the full suite.

## Known Pre-existing Exclusions

The coverage run omits generated and boilerplate-only modules. These are not regressions:
- `skyflow/generated/*` — Fern-generated REST client
- `skyflow/utils/validations/*`, `skyflow/vault/data/*`, `skyflow/vault/detect/*`
- `skyflow/vault/tokens/*`, `skyflow/vault/connection/*`, `skyflow/error/*`
- `skyflow/utils/enums/*`
- `skyflow/vault/controller/_audit.py`, `skyflow/vault/controller/_bin_look_up.py`

## Pipeline

### Step 1 — Lint
```bash
ruff check . --output-format=github
```
Expected: no output (clean). Report any errors — these block CI.

### Step 2 — Spell check
```bash
codespell
```
Report any unknown words. Add legitimate project terms to the ignore list rather than fixing them as typos.

### Step 3 — Tests
If `$ARGUMENTS` is set:
```bash
python -m coverage run --source=skyflow \
  --omit=skyflow/generated/*,skyflow/utils/validations/*,skyflow/vault/data/*,skyflow/vault/detect/*,skyflow/vault/tokens/*,skyflow/vault/connection/*,skyflow/error/*,skyflow/utils/enums/*,skyflow/vault/controller/_audit.py,skyflow/vault/controller/_bin_look_up.py \
  -m unittest $ARGUMENTS
```
Otherwise:
```bash
python -m coverage run --source=skyflow \
  --omit=skyflow/generated/*,skyflow/utils/validations/*,skyflow/vault/data/*,skyflow/vault/detect/*,skyflow/vault/tokens/*,skyflow/vault/connection/*,skyflow/error/*,skyflow/utils/enums/*,skyflow/vault/controller/_audit.py,skyflow/vault/controller/_bin_look_up.py \
  -m unittest discover
```
Report: tests run, failures, errors.

### Step 4 — Coverage report
```bash
python -m coverage report --show-missing
```
Flag any public interface module (`skyflow/client/`, `skyflow/vault/controller/`, `skyflow/service_account/`) below 80% coverage.

### Step 5 — Coverage gaps
For classes below complete coverage, identify missing scenarios:
- `None` / empty inputs
- Invalid types / wrong enum values
- Error paths (API rejection, validation failure)
- Concurrent / reuse scenarios

Write concrete `unittest.TestCase` method stubs (not full implementations) for each gap.

### Step 6 — Report

```
| Step          | Status    | Notes                        |
|---------------|-----------|------------------------------|
| Lint          | ✅ / ❌   | ...                          |
| Spell check   | ✅ / ❌   | ...                          |
| Tests         | ✅ / ❌   | N passed, M failed           |
| Coverage      | ✅ / ❌   | list modules below threshold |
```

Conclude with **READY TO MERGE** or **NEEDS FIXES** and a prioritised fix list.
