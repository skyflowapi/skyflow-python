---
name: code-review
paths: ["**/*.py"]
exclude: ["skyflow/generated/**", ".venv/**", "venv/**", "build/**", "dist/**", "skyflow.egg-info/**"]
context: fork
---

You are a senior engineer performing a thorough code review.

## Pre-requisite — Quality Gate (mandatory, evidence-gated)

Your FIRST action MUST be to invoke `/code-quality` via the Skill tool. Do not improvise by running `ruff`/`unittest`/`coverage` yourself — always go through `/code-quality`.

Your FIRST output block MUST be a `## Quality Gate` section containing EITHER:
- the `/code-quality` result summary, OR
- the exact reason it could not run (tooling missing, sandbox/permission block, etc.).

Do not emit ANY review content (scope, findings, tables) before that block exists. A review output with no `## Quality Gate` block is invalid and must be redone.

This gate is **non-blocking for the verdict**: a failed or un-runnable gate never aborts the review — record it and continue. But INVOKING it and SHOWING the result is not optional.

## Scope

Determine scope from `$ARGUMENTS` **in this exact order** — match the first case that applies and run its command before doing anything else. Do not fall through to the diff case unless `$ARGUMENTS` is empty.

**Base branch** — the diff base defaults to `main`. To review against a different base, pass `base=<branch>` in `$ARGUMENTS` (e.g. `base=develop`). Strip that token first, then interpret the remaining tokens below, substituting `<branch>` for `main` in the commands.

**1. `$ARGUMENTS` contains `full`** — review the **entire codebase** on the current branch, **not** a diff. Enumerate all source files:
```bash
git ls-files '*.py' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

**2. `$ARGUMENTS` is a file or directory path** (and not `full`) — review only that specific path. Do not expand scope beyond what was passed:
```bash
git ls-files '<path>' | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

**3. `$ARGUMENTS` is empty** — review only files changed in the current working diff (staged + unstaged) vs HEAD:
```bash
git diff HEAD --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
git diff --cached --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```
If that returns nothing (clean working tree), fall back to files changed on the current branch vs the base branch (default `main`):
```bash
git diff main...HEAD --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

State the resolved scope (`full` / `<path>` / `diff vs <base>`) and the file count at the top of your report so the chosen mode is auditable.

---

## Step 1 — Language Pattern Review

Review all files in scope against best practices. Check every rule category below.

Group findings by file and produce a table:

```
### path/to/file.py

| Severity | Category | Line | Finding |
|----------|----------|------|---------|
| Critical | Security      | 42  | exception silently swallowed |
| High     | Correctness   | 87  | mutable default argument shared across calls |
| Low      | Naming        | 103 | magic number 3600 — extract to a named constant |
```

| Severity | Meaning | Blocks merge? |
|---|---|---|
| **Critical** | Data loss, security breach, silent failure | Yes |
| **High** | Wrong behaviour / guaranteed runtime failure | Yes |
| **Medium** | Risky or unhandled input, missing safeguard | Yes |
| **Low** | Naming, style, minor maintainability | No |
| **Info** | Note / FYI | No |

**Category**: `Correctness`, `Edge case`, `Security`, `Language Pattern`, `Naming`, `Tests`, `Smell`.

---

### General rules (all languages)

**Naming**
- Names are accurate and proportional to scope: short locals, descriptive public names
- No single-letter names outside loop counters or well-known math variables
- Boolean names start with `is`, `has`, `should`, `can`, or similar
- Constants are `UPPER_SNAKE_CASE` and distinguishable from variables

**Error / exception handling**
- No exceptions silently swallowed without a comment explaining why
- Error messages include enough context to diagnose without a debugger
- No `sys.exit` / `os._exit` in library code — raise an exception and let the caller decide
- No `raise` of bare `Exception`/`BaseException` in library code; raise a specific, meaningful type

**API / interface design**
- Functions with more than 4 parameters use a config object / dataclass / keyword-only args
- Public constructors validate inputs and raise on invalid state
- Public functions, classes, and modules have docstrings

---

### Python-specific rules

> **Review for idiomatic Python (PEP 8 / PEP 20 / PEP 484), not just this checklist.** The rules below are the high-frequency items, **not exhaustive**. Evaluate the code against broader idioms — module/package layout, typing, dunder usage, generator vs list, comprehension readability — and flag idiomatic violations even when not itemised.

**Naming (PEP 8)**
- `snake_case` for functions/variables/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- Leading underscore (`_name`) marks internal API; a public name with no underscore is part of the contract — treat renames/removals as breaking
- Distance rule: the farther a name is used from where it's bound, the more descriptive it should be

**Exception handling**
- No bare `except:` — always catch a specific exception type (bare `except` also swallows `KeyboardInterrupt`/`SystemExit`)
- No `except Exception: pass` without a logged reason
- Chain with `raise NewError(...) from err` to preserve the original traceback
- Do not catch an exception only to re-raise a less specific one that loses context

**Mutability & defaults**
- No mutable default arguments (`def f(x=[])` / `def f(x={})`) — use `None` and initialise inside
- Do not mutate a caller-supplied list/dict/set unless the contract explicitly says so
- Dataclasses with mutable defaults use `field(default_factory=...)`

**Type hints**
- Public functions and methods have parameter and return type hints
- `Optional[T]` (or `T | None`) is used where `None` is a legal value — not left implicit
- Avoid `Any` where a concrete type or protocol would express intent

**Resource management**
- Files, sockets, DB connections, `requests`/`httpx` sessions opened via `with` (context manager) so they close on all paths including exceptions
- No reliance on refcount/GC for closing resources

**Correctness traps**
- No use of `==`/`!=` to compare with `None`, `True`, `False` — use `is`/`is not`
- No mutable class attributes used as if they were per-instance state
- Integer/float division (`/` vs `//`) matches intent
- f-strings/`.format` used instead of `%`-formatting for new code; no f-string without placeholders

**Structure**
- Public dataclasses / Pydantic models validate required fields; no half-constructed objects that raise at first use
- Module-level side effects (network calls, file I/O at import time) are avoided

---

## Step 1.5 — Runtime Safety

Check every function in scope for conditions that cause failures at runtime:

| Risk | Check |
|---|---|
| `None` dereference | Attribute/subscript access on a value that could be `None` without a guard |
| Key / index error | `dict[key]` / `list[i]` without membership or bounds check (prefer `.get()` / `len` guard) |
| Silent failure | Exception swallowed, or a return value that signals failure ignored |
| Resource leak | Files / sessions / connections opened without `with` or `try/finally` close |
| Divide by zero | Denominator could be zero from user input or a computed value |
| Process exit in library | `sys.exit` / `os._exit` / `quit()` — must only appear in entry-point/CLI code |

Report as **Edge Case** or **High** severity in the per-file table from Step 1.

---

## Step 2 — Code Smell Analysis

Invoke `/code-smell` for the same files in scope. Produce a per-file smell table, smell summary, and recommendation.

---

## Step 3 — Security Audit

Invoke `/code-security` for the same files in scope. Produce per-finding blocks, a summary table, and overall risk rating.

---

## Final Verdict

After all steps, close with:
1. A tech-debt summary table grouped by category (Patterns / Error Handling / Naming / Tests / Smells / Security)
2. **Quality Gate result** — PASS / FAIL / NOT RUN (with reason). Must match the `## Quality Gate` block above.
3. A verdict: `APPROVE` / `APPROVE WITH FIXES` / `REQUEST CHANGES`
4. Remind: run the quality gate again after any fixes before merging.
