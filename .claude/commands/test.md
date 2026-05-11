---
description: Full quality pipeline for the Skyflow Python SDK — lint, tests, coverage, and edge case analysis.
constraints:
  - "NEVER edit, create, or delete any file under skyflow/generated/. Always filter generated files before passing any file list to lint: git diff --name-only | grep -E '\\.py$' | grep -v 'generated'. If analysis touches generated code, report it as an observation only."
---

Run the full Skyflow Python SDK quality pipeline and report results. Target (optional — specific test file, module path, or keyword pattern): $ARGUMENTS

> **IMPORTANT — Generated code boundary**
> `skyflow/generated/` contains Fern-generated REST client code. **Never modify any file inside `skyflow/generated/`**. If analysis or test generation touches generated code, report it as an observation only — do not edit, create, or delete any file under that path.

Execute the following steps in order. Stop and report clearly if any step fails.

---

## Step 1 — Lint

Lint only the files that have changed, not the entire repo.

First, get the list of changed `.py` files, excluding generated code:
```bash
git diff --name-only HEAD | grep -E '\.py$' | grep -v 'generated'
```
If that returns nothing (e.g. all changes are staged or no unstaged diff), fall back to staged files:
```bash
git diff --name-only --cached | grep -E '\.py$' | grep -v 'generated'
```
If `$ARGUMENTS` is a file path, use that file directly instead.

Then run ruff on those files:
```bash
.venv/bin/python -m ruff check <changed files>
```

If ruff is not installed, fall back to flake8:
```bash
.venv/bin/python -m flake8 <changed files>
```

Report any violations including file name and line number. A clean lint is required before proceeding.

---

## Step 2 — Tests

If `$ARGUMENTS` is provided and is a file or directory path, run only matching tests:
```bash
.venv/bin/python -m pytest "$ARGUMENTS" --import-mode=importlib -v
```

If `$ARGUMENTS` is a keyword pattern (no path separators), use `-k`:
```bash
.venv/bin/python -m pytest tests/ --import-mode=importlib -k "$ARGUMENTS" -v
```

Otherwise run the full suite:
```bash
.venv/bin/python -m pytest tests/ --import-mode=importlib -q
```

Report the count of passed, failed, and skipped tests. If any test fails, print the failure message in full and stop.

---

## Step 3 — Coverage analysis

Run the test suite with coverage, scoped to the `skyflow/` package and excluding generated code:
```bash
.venv/bin/python -m pytest tests/ --import-mode=importlib \
  --cov=skyflow \
  --cov-report=term-missing \
  --cov-omit="skyflow/generated/*" \
  -q
```

After tests complete, analyze the coverage output:
- Report overall line coverage %
- **Line coverage must be 100%** for all modules under `skyflow/` (excluding `skyflow/generated/`) — flag every file below 100%
- Flag any file with branch coverage below 80% if branch coverage is enabled
- For every flagged file, list the exact uncovered line numbers and what scenario they represent

---

## Step 4 — Edge case analysis and test generation

For every file under `skyflow/` that has line coverage below 100%, **or** for the target module if `$ARGUMENTS` is provided:

### 4a — Identify uncovered edge cases

Read the source file and its corresponding test file in `tests/`. For each uncovered branch or line, identify the missing scenario. Focus on:
- `None` inputs to public methods
- Empty strings, empty lists, zero or negative numbers
- Wrong types passed where a specific type is expected
- Error paths (`SkyflowError` raises) that are never triggered in tests
- Boundary conditions (exactly at limit vs. one over)
- Credential fields missing, malformed, or using snake_case vs camelCase variants
- Validator branches that check presence and type separately but only one branch is tested

List each gap as:
```
UNCOVERED: <file>:<line-range> — <what scenario is missing>
```

### 4b — Write the missing unit tests

For each identified gap, write a concrete test case using the project's existing conventions:
- Test files live in `tests/vault/controller/`, `tests/service_account/`, `tests/utils/`, or `tests/vault/` — pick the nearest existing test file
- Follow the `class TestXxx(unittest.TestCase)` structure used throughout the project
- Mock external dependencies (API calls, `generate_bearer_token`, `AuthClient`) using `@patch` decorators, matching the pattern in existing tests
- Each test must: arrange inputs → call the method → assert the outcome (return value or raised `SkyflowError`)
- Use `self.assertRaises(SkyflowError)` with `.exception.message` assertions to match existing test style
- Do **not** remove or modify existing tests

Output new tests as a ready-to-paste code block, clearly labelled with the target test file path.

---

## Step 5 — Report

Produce a summary table:

| Step | Status | Notes |
|------|--------|-------|
| Lint | PASS / FAIL | violation count |
| Tests | PASS / FAIL | X passed, Y failed, Z skipped |
| Coverage | % | files below 100% threshold listed |
| Edge cases | n found | n tests written |

End with: **READY TO MERGE** or **NEEDS FIXES**, followed by a bullet list of what must be addressed before merging.
