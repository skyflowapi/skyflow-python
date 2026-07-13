---
name: code-quality
paths: ["**/*.py"]
exclude: ["skyflow/generated/**", ".venv/**", "venv/**", "build/**", "dist/**", "skyflow.egg-info/**"]
context: fork
---

<!--
context: fork runs this command in a subagent with a clean context window — only the
result returns. The subagent runs non-interactively and cannot answer approval prompts,
so the gate commands below are pre-authorized in this repo's .claude/settings.json.
Without those allows, lint/test/coverage report as BLOCKED instead of running.
-->

Run the Python quality pipeline.

Determine scope from `$ARGUMENTS` **in this exact order** — match the first case that applies and run its steps before doing anything else. Do not fall through to the diff case unless `$ARGUMENTS` is empty.

**1. `$ARGUMENTS` contains `full`** — run all pipeline steps against the **entire codebase** (the `skyflow` package), no diff filtering.

**2. `$ARGUMENTS` is a path** (e.g. `skyflow/vault/controller`) — run all pipeline steps against that path only.

**3. `$ARGUMENTS` is empty** — run against `.py` files changed in the working tree **or** committed on this branch vs `main`. Take the **union** of both, so committed branch work is never missed even when the working tree is dirty (a dirty tree must NOT suppress branch-vs-`main` scope):
```bash
{ git diff HEAD --name-only; git diff --cached --name-only; git diff main...HEAD --name-only; } \
  | grep '\.py$' \
  | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/' \
  | sort -u
```
Derive scope from those files. If the union is empty, there is nothing changed to gate — report `diff` scope with no files and skip the pipeline.

State the resolved scope (`full` / `<path>` / `diff`) at the top of your report so the chosen mode is auditable.

## Coverage Requirements

All AI-generated code must reach 100% coverage — every line and every branch. This rule is identical across languages: any AI-generated code below 100% line or branch coverage is a blocker.

Flag any such gap as **NEEDS FIXES**.

---

## Pipeline

### Step 1 — Build (import/compile check)
```bash
python -m compileall -q skyflow 2>&1 | tail -20
```
Expected: no output (everything compiles). A `SyntaxError` here is a blocker. This is the Python equivalent of a build — it does not install the package. If you need a full packaging check, `python -m build` (or `python setup.py sdist bdist_wheel`) mirrors CI, but do not run it as part of the standard gate unless packaging is in scope.

### Step 2 — Spell check
```bash
codespell 2>&1 | tail -30
```
The repo ships a [.codespellrc](.codespellrc) — honour its `skip`/`ignore-words` config. Report any misspellings at blocker severity only when they appear in user-facing strings or public API names; otherwise **Low**. Add legitimate domain terms to `.codespellrc` rather than "fixing" them.

### Step 3 — Lint
```bash
ruff check . --output-format=github 2>&1 | tail -30
```
`ruff.toml` selects `N` (pep8-naming) and `PLR2004` (magic value) with `line-length = 120` and excludes `skyflow/generated`, `tests`, and `samples`. Report every violation — these are blockers. If a path scope was given, you may narrow to `ruff check <path>`.

### Step 4 — Tests
This repo uses **`unittest`** (not pytest), run under `coverage`, matching [.github/workflows/shared-tests.yml](.github/workflows/shared-tests.yml):
```bash
python -m coverage run \
  --source=skyflow \
  --omit='skyflow/generated/*,skyflow/utils/validations/*,skyflow/vault/data/*,skyflow/vault/detect/*,skyflow/vault/tokens/*,skyflow/vault/connection/*,skyflow/error/*,skyflow/utils/enums/*,skyflow/vault/controller/_audit.py,skyflow/vault/controller/_bin_look_up.py' \
  -m unittest discover 2>&1 | tail -60
```
Report: tests run, failures/errors, PASS summary. Flag any failure beyond the known pre-existing baseline.

### Step 5 — Coverage analysis
```bash
python -m coverage report --show-missing 2>&1 | tail -40
```
Lines with a `Missing` column show uncovered line ranges. For every function touched in this session:
- Verify a corresponding test exists
- Verify positive path (happy path) AND negative path (error/validation rejection) are covered
- Verify every branch (`if` / `for` / `try/except` / `match`) is exercised

List all gaps. Any gap on AI-generated code is a **blocker**. (Note: the `--omit` list above intentionally excludes generated and boilerplate modules from the coverage denominator — do not flag those as gaps.)

### Step 6 — Edge case identification
For any module below 100% coverage, identify missing scenarios:
- `None` / empty / whitespace inputs to public functions
- Invalid enum / sentinel values
- Concurrent access (if state is shared)
- Error paths (network failure, missing input, expired token)

List each missing scenario as a coverage gap.

### Step 7 — Vulnerability scan
```bash
pip-audit 2>&1 | tail -30
```
If `pip-audit` is not installed, report the scan as **skipped** (install with `pip install pip-audit` to enable) — do not auto-install during the pipeline. Report every reachable advisory; a directly-reachable CVE in a runtime dependency is a **blocker**.

If the repo's semgrep ruleset is present, also run:
```bash
semgrep --config .semgreprules --error 2>&1 | tail -30
```
If `semgrep` is not installed, report it as **skipped** (`pip install semgrep`) — do not auto-install.

### Step 8 — Report

```
| Step             | Status    | Notes                             |
|------------------|-----------|-----------------------------------|
| Build (compile)  | ✅ / ❌   | ...                               |
| Spell check      | ✅ / ❌   | ...                               |
| Lint (ruff)      | ✅ / ❌   | ...                               |
| Tests            | ✅ / ❌   | N passed, M failed                |
| Coverage (100%)  | ✅ / ❌   | list functions with gaps          |
| Vuln scan        | ✅ / ❌ / ⏭️ | CVEs found / none / skipped     |
```

Conclude with **READY TO MERGE** or **NEEDS FIXES** and a prioritised fix list.
