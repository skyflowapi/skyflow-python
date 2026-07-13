---
name: code-smell
paths: ["**/*.py"]
exclude: ["skyflow/generated/**", ".venv/**", "venv/**", "build/**", "dist/**", "skyflow.egg-info/**"]
context: fork
---

You are a senior Python engineer performing a code smell analysis.

## Scope

Determine scope from `$ARGUMENTS` **in this exact order** — match the first case that applies and run its command before doing anything else. Do not fall through to the diff case unless `$ARGUMENTS` is empty.

**Base branch** — the diff base defaults to `main`. To analyse against a different base, pass `base=<branch>` in `$ARGUMENTS` (e.g. `base=develop`). Strip that token first, then interpret the remaining tokens below, substituting `<branch>` for `main` in the commands.

**1. `$ARGUMENTS` contains `full`** — analyse the **entire codebase** on the current branch, not a diff. Enumerate all source files:
```bash
git ls-files '*.py' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

**2. `$ARGUMENTS` is a file or directory path** (and not `full`) — analyse only that specific path:
```bash
git ls-files '<path>' | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

**3. `$ARGUMENTS` is empty** — analyse only files changed in the current working diff:
```bash
git diff HEAD --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
git diff --cached --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```
If the working tree is clean, fall back to files changed on the current branch vs the base branch (default `main`):
```bash
git diff main...HEAD --name-only | grep '\.py$' | grep -v 'skyflow/generated/\|\.venv/\|venv/\|build/\|dist/\|skyflow\.egg-info/'
```

State the resolved scope (`full` / `<path>` / `diff vs <base>`) and the file count at the top of your report so the chosen mode is auditable.

---

## Spell check

```bash
codespell 2>&1 | tail -30
```
The repo ships a [.codespellrc](.codespellrc) — honour its `skip`/`ignore-words`. Report any spelling violations at **Smell** severity in the per-file table. Add legitimate project-specific or domain terms to `.codespellrc` rather than marking them as typos. If `codespell` is not installed, note "spell check skipped (codespell not installed)" rather than omitting it silently.

---

## What Are Code Smells

Code smells are structural signals — they do not necessarily mean the code is broken, but they indicate areas of technical debt, reduced readability, or future maintenance risk. All findings are reported at **Smell** severity and do not block merge unless they indicate a design violation.

---

## Smell Catalogue

### Function & File Size

**Long function** — any function over 40 lines.
Signal: the function is doing too much. Candidate for decomposition into named helpers.

**Long file / module** — any file over 400 lines.
Signal: the module may be taking on too many responsibilities. Check if it can be split by concern.

**Large parameter list** — more than 4 parameters on a function.
Signal: consider a dataclass, an options object, or keyword-only arguments grouping related parameters.

---

### Responsibility Violations

**Business logic in data classes**
Dataclasses / Pydantic models / plain data holders should not contain conditional logic, field transformations, or computation beyond simple derived properties. Flag any such methods.

**Validation outside a dedicated validation layer**
This repo has a validation layer under `skyflow/utils/validations`. Any `if x is None: raise ...` / `if not x: raise ...` guard outside that layer (in controllers, clients, data holders) is misplaced.

**Message strings inline in application logic**
String literals passed directly to `logging.*`, exception constructors, or `raise` that could be named constants are a responsibility smell — especially when the same or similar strings appear more than once.

---

### Control Flow

**Deep nesting** — more than 3 levels of `if` / `for` / `while` / `try` / `with` nesting.
Signal: extract inner blocks to named private functions or use early returns / guard clauses.

**Long if-elif chains** — more than 4 branches on the same value.
Signal: consider a dict-based dispatch, `match` statement, or polymorphism.

**Repeated None/empty checks**
Multiple consecutive `is None` / `if not x` guards on the same value that could be collapsed or replaced with an early return.

---

### Data

**Magic numbers**
Literal integers or durations (`25`, `64`, `3600`) without a named constant. Ruff's `PLR2004` flags these — extract to a module-level constant. Report literals `PLR2004` would catch.

**Repeated string literals**
Any string appearing more than once that should be a named constant.

**Mutable default argument**
`def f(x=[])` / `def f(x={})` — the default is shared across calls. Use `None` and initialise inside. (Correctness-adjacent, but report as a smell here.)

---

### Dead Code

**Unused private functions** — module-private (`_name`) functions with no callers in the same module.

**Unused imports / variables** — ruff `F401` (unused import) and `F841` (unused local) catch these. Flag any seen.

**Unreachable code** — statements after `return` / `raise` / `continue` / `break` in the same branch.

**Commented-out code** — blocks of commented code without a `# TODO: [ticket]` explaining why they are kept.

---

### Typing & Interface Design

**Class with too many public methods / responsibilities** — a class exposing many unrelated public methods.
Signal: violates single-responsibility; split into narrower collaborators.

**`Any` where a concrete type or `Protocol` would work**
Using `Any` as a parameter or return type loses type safety. Flag unless the function is genuinely type-agnostic (e.g. a serialiser).

**Bare containers as public return types**
Returning raw `dict`/`tuple` where a dataclass or typed model would make the contract clearer.

---

### Constructor Patterns

**Class with required fields but no validation / factory**
Callers can construct a half-initialised instance that raises at first use. Public classes with required fields should validate in `__init__` (or a `NewXxx`/`from_*` classmethod).

**`__init__` doing heavy work**
Network calls, file I/O, or expensive computation in `__init__` — prefer a factory/classmethod so construction stays cheap and testable.

---

### Writing Functions

For each changed function, apply this 5-step checklist:
1. Can you follow what the function does in one reading? If yes, stop.
2. High cyclomatic complexity (deep nesting, many branches)? → candidate for decomposition into named helpers.
3. Would a common data structure (dict, set, dataclass) make this simpler and more robust?
4. Hidden untested dependencies or values that could be factored into parameters?
5. Is the function name the best possible? Brainstorm 3 alternatives; flag if the current name is weaker.

---

### Test Smells

**`unittest.skip` / `@skip` / `self.skipTest(...)` without a `# TODO: [ticket]` comment**
Skipped tests silently rot with no path back. Every skip must reference a ticket.

**`time.sleep` in tests**
Non-deterministic; use mocks, `unittest.mock`, or explicit synchronisation instead.

**Test body with no assertions**
A test that calls functions but never asserts (`assert*`) always passes and catches nothing.

**Over-broad mocking / patching that asserts nothing about behaviour**
A test that patches everything and only checks the mock was called can pass while the real code is broken.

**100% coverage required**
All AI-generated code must have 100% line and branch coverage. Flag any AI-generated function with uncovered statements or branches. Report as **Smell** with the specific function and line range.

---

### Comments

**Explains what, not why**
A comment that restates what the code does (`# loop over records`) adds no value. Only flag comments that explain the *what* without explaining *why*.

**Stale comment / docstring**
A comment or docstring that contradicts the current code — references a removed parameter, old function name, or changed behaviour.

---

## Output Format

Group findings by file:

```
### path/to/file.py

| Smell                     | Line | Detail                                                        |
|---------------------------|------|---------------------------------------------------------------|
| Long function             | 42   | process_response() is 67 lines — decompose                   |
| Magic number              | 103  | Literal 64 — extract to a named constant                     |
| Inline string literal     | 210  | "user id is required" appears 3 times — extract to const     |
| Mutable default arg       | 15   | def build(headers={}) — use None and initialise inside       |
| Dead code                 | 315  | private _build_auth_header() has no callers                  |
```

End with a **Smell Summary** table:

```
| Category              | Count | Files affected              |
|-----------------------|-------|-----------------------------|
| Long functions        | 2     | response.py                 |
| Magic numbers         | 3     | validations.py              |
| Inline string literal | 5     | controller.py               |
| Dead code             | 2     | helpers.py                  |
```

Close with a recommendation: **CLEAN** / **MINOR DEBT** / **SIGNIFICANT DEBT** and a one-sentence summary.
