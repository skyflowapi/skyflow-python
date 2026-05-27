---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
paths:
  - skyflow/**/*.py
  - tests/**/*.py
---

# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing a major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing a complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Choose the right review type for this project:**

| Change type | Use |
|---|---|
| SDK logic, patterns, naming, tests | `/code-review` — runs SDK checks + smell + security |
| Structural debt only | `/code-smell` — standalone smell analysis |
| Auth, credentials, tokens, HTTP | `/code-security` — standalone security audit |
| Full review via subagent | Dispatch with template below |

For a full feature branch vs main:
```bash
BASE_SHA=$(git merge-base main HEAD)
HEAD_SHA=$(git rev-parse HEAD)
```

For security-sensitive changes (auth, credentials, bearer tokens, HTTP headers) — dispatch both quality and security:
```bash
/code-review skyflow/service_account/
/code-security skyflow/service_account/
```

**3. Dispatch code reviewer subagent:**

Use Agent tool with `general-purpose` type and fill in the template placeholders:

**Placeholders:**
- `{DESCRIPTION}` — Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` — What it should do
- `{BASE_SHA}` — Starting commit
- `{HEAD_SHA}` — Ending commit

**4. Act on feedback:**
- Fix Critical issues immediately
- Fix Bug / Edge Case issues before proceeding
- Note Quality / Smell issues for later
- Push back if the reviewer is wrong (with reasoning)

## Example

```
[Just completed: Add FileUploadRequest deprecation shim]

You: Let me request code review before proceeding.

BASE_SHA=$(git merge-base main HEAD)
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added *args shim to FileUploadRequest for backward-compatible positional arg order
  PLAN_OR_REQUIREMENTS: Old order (table, skyflow_id, column_name) must still work with DeprecationWarning
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean shim, correct stacklevel=2, good test coverage
  Issues:
    Bug: Magic value 2 in len(args) >= 2 — PLR2004 ruff violation
    Quality: Warning message doesn't mention what to use instead
  Assessment: Approve with fixes

You: [Fix ruff violation and update warning message]
[Continue to next task]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to the next task

**Executing Plans:**
- Review after each task or at natural checkpoints
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Bug / Edge Case issues
- Argue with valid technical feedback

**If reviewer is wrong:**
- Push back with technical reasoning
- Show code / tests that prove it works
- Request clarification
