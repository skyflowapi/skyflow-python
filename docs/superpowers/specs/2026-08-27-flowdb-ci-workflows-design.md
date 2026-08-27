# FlowDB CI/CD workflows for skyflow-python (SK-3119)

## Context

skyflow-python is currently a single flat package (`skyflow/`, `setup.py` at repo
root, one PyPI distribution). skyflow-java has already split into three Maven
modules under one repo — `common`, `skyvault`, `flowvault` — each independently
versioned and released, with its own PR/release/internal-release workflows. This
spec ports that CI/CD model to skyflow-python, in preparation for skyflow-python
adopting the same `common/skyvault/flowvault` folder split.

**Non-goal:** this spec does not create the `common/`, `skyvault/`, `flowvault/`
folders or move any code. The workflows and scripts below are written for that
target layout and will only build/test/release successfully once a separate
migration PR creates it. This branch is therefore only ever meant to be merged
into `main` together with (or immediately before) that migration PR — never
merged alone. It has NOT been made safe to sit on `main` on its own: as
implemented, `shared-tests.yml`'s per-module loop skips every module that
doesn't exist yet and exits 0, so `pr.yml`/`main.yml` would report green while
running zero unit tests; and the release workflows resolve `release/*`
pushes and legacy bare-`x.y.z` tags to module `skyvault`, which then hard-fails
at `skyvault/setup.py not found` — meaning today's live release path (JFrog
and PyPI) would stop working with no fallback until the migration lands. Both
were confirmed and accepted by the repo owner as out of scope for this spec
specifically because the merge-together constraint holds; if that constraint
ever changes (i.e. this needs to land on `main` before the migration PR is
ready), an interim root-package fallback must be designed first — don't merge
this alone without one.

Reference implementation: `/home/devb/skyflow/skyflow-java/.github/workflows/`
(`pr.yml`, `pr-flowvault.yml`, `main.yml`, `release.yml`, `internal-release.yml`,
`shared-build-and-deploy.yml`) and `/home/devb/skyflow/skyflow-java/scripts/`
(`bump_version.sh`, `current_module_version.sh`).

## Decisions (confirmed with user)

- **Scope:** workflows and supporting scripts only, no code/folder migration.
- **Trigger model:** mirror Java exactly — GitHub Release publish event with
  tag `<module>/v<semver>[-beta.N]` for public/beta (collapsed into one
  workflow); `push` to `<module>-release/*` branches for internal/JFrog.
- **Package naming:** `skyvault` keeps publishing as PyPI package `skyflow`
  (backward compatible with the current single package). `flowvault` publishes
  as a new package, `skyflow-flowvault-python`. `common` is never published on
  its own — it's a local path dependency bundled into whichever module's wheel
  needs it, same as Java's `common` module.
- **JFrog target:** both modules publish into the existing JFrog PyPI repo
  (`https://prekarilabs.jfrog.io/artifactory/api/pypi/skyflow-python/`) under
  their respective package names — no new Artifactory repo.

## Workflows

### `pr.yml` (replaces `ci.yml`)

- Trigger: `pull_request` (any).
- `check-commit-message` job: unchanged from today's `ci.yml` (JIRA-ID commit
  message check).
- `test` job: calls `shared-tests.yml`, which builds+tests all three modules
  (`common`, `skyvault`, `flowvault`) and uploads three separate Codecov flags.
- `spellcheck` job: repo-wide `codespell`, unchanged from today.

### `pr-flowvault.yml` (new)

- Trigger: `pull_request` targeting `main` or `flowvault-release/**`, only
  when paths `flowvault/**`, `common/**`, or `flowvault/setup.py` change.
- Scoped build+test of `flowvault` (+ `common`) only — mirrors Java's
  `pr-flowvault.yml` intent (skyvault-only PRs are already covered by the
  full `pr.yml` run; this is the fast-path gate for flowvault-focused work).

### `main.yml`

- Trigger: `push` to `main`.
- Same full three-module build+test as `pr.yml`'s `test` job (calls
  `shared-tests.yml`).

### `release.yml` (public/beta, replaces `release.yml` + `beta-release.yml`)

- Trigger: `release: published`.
- `resolve-release` job parses `github.event.release.tag_name` as
  `<module>/v<semver>[-beta.N]`:
  - module: `skyvault` or `flowvault` (anything else → hard error, same as
    Java — `common` is never releasable).
  - kind: `beta` if the version has a `-beta.N` suffix, else `public`.
  - branch: `github.event.release.target_commitish` (required — same
    ancestor-of-branch validation Java's shared workflow does).
- `build-and-deploy` job calls `shared-build-and-deploy.yml` with
  `module`, `version`, `release-branch`, publishing to real PyPI.

### `internal-release.yml` (JFrog)

- Trigger: `push` to `skyvault-release/*`, `flowvault-release/*`, or legacy
  `release/*` (maps to `skyvault`), excluding `[AUTOMATED]` commits (loop
  guard, same as Java).
- `resolve-module` job maps branch name → module via explicit `case`
  statement (no catch-all — a wrong default silently publishes the wrong
  package).
- `build-and-deploy` job calls `shared-build-and-deploy.yml` with
  `tag: internal`, publishing to the JFrog PyPI repo.

## Reusable workflows

### `shared-tests.yml`

- Input: `python-version` (unchanged).
- Loops over `common skyvault flowvault`:
  - `pip install`/build each module's own `setup.py` (skip a module
    gracefully with a notice if its `setup.py` doesn't exist yet — keeps this
    workflow from hard-failing pre-migration in contexts where only a subset
    of modules matters, though `pr.yml`'s full run still expects all three).
  - Run that module's unit tests under `coverage run --source=<module>`.
  - Upload Codecov with a per-module flag (`common`/`skyvault`/`flowvault`),
    matching Java's per-module JaCoCo upload split.
- `codespell` and `ruff check` remain repo-wide, run once (not per module).

### `shared-build-and-deploy.yml`

- Inputs: `module` (required), `version` (optional — set for beta/public,
  parsed from the tag), `release-branch` (optional — required for beta/
  public), `tag` (`internal`/`beta`/`public`), `dry-run` (optional bool).
- Secrets: reuses the repo's existing secret names —
  `PYPI_PUBLISH_TOKEN` (public/beta), `JFROG_USERNAME`/`JFROG_PASSWORD`
  (internal), `PAT_ACTIONS` (bump-commit push). No new secrets need to be
  provisioned, and no test-fixture secrets are needed here: unlike Maven's
  `deploy` lifecycle, `python setup.py sdist bdist_wheel` + `twine upload`
  never execute the test suite, so there's nothing for `.env`/
  `credentials.json` to feed — tests already gate this code via `pr.yml`/
  `main.yml` before a release branch or tag is ever cut. This is a deliberate
  divergence from Java's shared-build-and-deploy, not an oversight.
- Steps (module-scoped versions of the current single-package steps):
  1. Checkout with `pat-actions` token (admin bypass for the bump-commit
     push, same as today).
  2. For beta/public: validate `release-branch` is set and the tagged commit
     is an ancestor of `origin/<release-branch>`.
  3. Resolve base version: `inputs.version` if set (beta/public) else
     `ci-scripts/current_module_version.sh <module>` (internal) — never a
     bare `git describe`/previous-tag lookup, since tags are per-module and a
     repo-wide "previous tag" would leak another module's version in.
  4. `ci-scripts/bump_version.sh <base_version> [<commit-sha>] <module>`.
  5. Commit `[AUTOMATED] Private Release ...` (internal, force-push to
     `github.ref_name`) or `[AUTOMATED] Public Release - ...` (beta/public,
     push to `release-branch`) — skip the commit if nothing changed (module
     already at target version), same as Java.
  6. Build `<module>`'s sdist/wheel (`cd <module> && python setup.py sdist
     bdist_wheel`) and `twine upload` to PyPI (beta/public) or the JFrog PyPI
     repo (internal) — `dry-run: true` builds and validates everything but
     skips the actual `twine upload` and the bump-commit push (PyPI publishes
     are immutable, same rationale as Java's `mvn verify` vs `deploy` split).

## Supporting scripts (`ci-scripts/`)

### `bump_version.sh` (rewritten, module-aware)

- New signature: `bump_version.sh <version> [<commit-sha>] <module>`.
- Patches `<module>/setup.py`'s `current_version = '...'` line.
- If `<module>/setup.py`'s package declares a runtime version constant file
  (searched as `<module>/**/_version.py`, matching today's
  `skyflow/utils/_version.py` convention), patches its `SDK_VERSION = '...'`
  too — skipped with a `::notice::` if no such file is found yet, so the
  script stays correct both before and after the eventual code migration.
- With `<commit-sha>` given: appends `.dev0+<sha>` (internal releases) —
  unchanged suffix format from today's single-package script.

### `current_module_version.sh` (new)

- Python port of Java's script of the same name: reads `<module>/setup.py`'s
  `current_version = '...'` line, strips any trailing `.devN+<sha>` suffix,
  prints the bare version. Read-only, never touches git tags — used by
  internal releases so a stray tag can never leak another module's version
  into the wrong package's bump.

## Testing/validation

Since the target folders don't exist yet, these workflows can't be exercised
end-to-end in this repo today. Validation for this change is:
- `actionlint` (or GitHub's workflow syntax check) on every new/changed
  `.yml` file.
- `shellcheck` on `bump_version.sh` and `current_module_version.sh`.
- Manual read-through diff against the Java reference workflows to confirm
  parity of trigger conditions, guard rails (loop-prevention, ancestor
  checks, explicit-no-catch-all module resolution), and dry-run behavior.
Full functional validation happens once the actual `common/skyvault/flowvault`
migration PR lands and a real PR/tag can exercise these workflows.
