---
name: code-smell
description: Structural smell analysis + spell check — long methods, dead code, misplaced validation, deep nesting, magic numbers. Does not check patterns or security.
paths:
  - skyflow/**/*.py
---

You are a senior engineer performing a code smell analysis on the Skyflow Python SDK.

## Scope

Use `$ARGUMENTS` to determine scope:
- A file or directory path — analyse only that path
- Empty / default — analyse files changed on current branch vs `main`:
  ```bash
  git diff main...HEAD --name-only | grep '\.py$' | grep -v 'generated'
  ```

**Skip entirely:** `skyflow/generated/` — Fern-generated REST client, read-only.

---

## Spell check

Before analysing smells, run codespell on the files in scope:

```bash
codespell skyflow/ tests/ samples/ docs/ CLAUDE.md
```

Report any spelling violations at **Smell** severity in the per-file table. Add legitimate project-specific terms to `.codespell-ignore` rather than treating them as typos.

---

## What Are Code Smells

Code smells are structural signals — they do not necessarily mean the code is broken, but they indicate areas of technical debt, reduced readability, or future maintenance risk. All findings are reported at **Smell** severity and do not block merge unless they indicate a design violation.

---

## Smell Catalogue

### Method & Class Size

**Long method** — any method over 50 lines.
Signal: the method is doing too much. Candidate for decomposition into named private helpers.

**Large parameter list** — more than 5 parameters on a method.
Signal: consider a request dataclass or keyword-only arguments to group related parameters.

---

### Responsibility Violations

**Business logic in Request/Response classes**
Request and Response classes are data holders — they carry data, nothing more. Flag any conditional logic, field transformation, or computation beyond simple attribute assignment in `__init__`.

**Validation outside `_validations.py`**
Any `if x is None: raise SkyflowError(...)` outside `skyflow/utils/validations/` is misplaced validation. All request validation must live in `validate_*()` functions in `_validations.py`.

---

### Control Flow

**Deep nesting** — more than 3 levels of `if` / `for` / `try` nesting.
Signal: extract inner blocks to named private methods or use early returns.

**Long if-else chains** — more than 4 branches on the same condition.
Signal: consider a dispatch `dict` or separate handler methods.

**Null checks scattered**
Multiple consecutive `if x is None` guards that could be replaced with an early return guard clause.

---

### Data

**Magic numbers**
Literal integers or sizes (e.g. `25`, `3600`, `100`) in comparisons or logic without a named constant. Use `UPPER_SNAKE_CASE` constants in `skyflow/utils/constants.py`.

**Mutable default arguments**
`def f(self, items=[], config={})` — mutable defaults are shared across all calls. Replace with `None` and initialise in the body.

**Temporary attribute**
A `self.xxx` attribute that is only set in certain code paths and `None` the rest of the time. Should be a local variable or method parameter instead.

---

### Dead Code

**Unused private methods** — private methods (`_xxx`) with no callers.

**Unused imports** — run `ruff check --select=F401` to identify.

**Unreachable code** — code after `return` / `raise` in the same branch.

**Commented-out code** — blocks of commented code without explanation. Remove entirely or add a `# TODO: [ticket]` with context.

---

### Comments

**Explains what, not why**
A comment that restates what the code does (`# get the vault ID`) adds no value. Flag comments that explain *what* without explaining *why*.

**Stale comment**
A comment that contradicts the current code — e.g. references a removed parameter, an old method name, or a behaviour that has changed.

---

## Output Format

Group findings by file:

```
### skyflow/path/to/file.py

| Smell                     | Line | Detail                                                      |
|---------------------------|------|-------------------------------------------------------------|
| Long method               | 42   | _process_insert_response() is 67 lines — decompose         |
| Business logic in Response| 88   | __init__ renames skyflow_id — move to controller            |
| Magic number              | 103  | Literal 25 — extract to MAX_QUERY_RECORDS constant          |
| Stale comment             | 210  | References removed tokenized_data field                     |
| Dead code                 | 315  | Private method _build_headers() has no callers              |
```

End with a **Smell Summary** table:

```
| Category              | Count | Files affected              |
|-----------------------|-------|-----------------------------|
| Long methods          | 2     | _vault.py                   |
| Business logic in DTO | 1     | _query_response.py          |
| Magic numbers         | 3     | _validations.py             |
| Dead code             | 2     | _utils.py                   |
```

Close with a recommendation: **CLEAN** / **MINOR DEBT** / **SIGNIFICANT DEBT** and a one-sentence summary.
