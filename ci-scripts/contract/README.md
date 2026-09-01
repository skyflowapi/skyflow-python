# Public API contract tests

Each published package has a committed **public API contract baseline**, and CI fails a PR that
changes the public surface without updating it. This is the Python counterpart of the Java SDK's
`japicmp` contract gate, built on [`griffe`](https://mkdocstrings.github.io/griffe/) (static Python
API analysis).

| Module | Package | Baseline |
|---|---|---|
| `skyvault` | `skyflow` | `skyvault/api-report/skyflow.api.json` |
| `flowvault` | `skyflow_flowvault` | `flowvault/api-report/skyflow_flowvault.api.json` |

## What is "the contract"

An explicit **allowlist** of public modules (defined in `griffe_contract.py`, mirroring Java's
`<includes>`), not a blocklist. Everything outside it — `generated/` (the Fern REST client),
internal `utils` helpers, `_version`, underscore-prefixed names — is internal and free to change.
For each allowlisted module the snapshot records every public class, function, enum value, and each
class's `__init__` signature and public members.

## Workflow

- **On every PR** (`.github/workflows/contract-tests.yml`, one job per module) the current surface is
  regenerated and compared to the committed baseline. Removed/changed entries are **breaking**; added
  entries are **new public surface**. Any drift fails the job.
- **When you intentionally change the public API**, regenerate and commit the baseline:

  ```bash
  ci-scripts/contract-snapshot-update.sh skyvault      # or flowvault, or omit for both
  ```

  Review the `api-report/*.api.json` diff and commit it with your code change, so a reviewer sees
  exactly what contract change was approved (CI also posts that diff as a PR comment).
- **skyvault is additionally guarded against the last public release**:
  `griffe check skyflow -s skyvault -a skyflow==<release>` fails if skyvault breaks any API a consumer
  of the released `skyflow` relies on. Bump `SKYVAULT_RELEASE` in the workflow when skyvault releases.

## Running locally

```bash
pip install "griffe[pypi]==2.2.0"
python ci-scripts/contract/griffe_contract.py check skyvault skyvault/api-report/skyflow.api.json
python ci-scripts/contract/griffe_contract.py check flowvault flowvault/api-report/skyflow_flowvault.api.json
```

No wheel build is needed — griffe analyzes the source statically; the repo root is on the search path
so `common` re-exports (e.g. `SkyflowError`) resolve.

## Known limitation

`Skyflow` and the `Vault`/`VaultController` classes are created through the `make_skyflow_class(...)`
factory, so static analysis cannot see their methods — the snapshot records the factory construction,
not `vault()`, `builder()`, `insert()`, etc. Those surfaces are covered by the behavioral
`tests/contract/` suite and the unit tests instead. This is a static-analysis limit, not a gap in the
factory's runtime API.
