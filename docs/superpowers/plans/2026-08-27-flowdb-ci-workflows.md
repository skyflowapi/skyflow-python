# FlowDB CI/CD Workflows (SK-3119) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port skyflow-java's `common`/`skyvault`/`flowvault` PR, public-release and internal/JFrog-release CI workflow model to skyflow-python, so it's ready the moment skyflow-python's code migrates into that same three-folder layout.

**Architecture:** Two reusable `workflow_call` workflows (`shared-tests.yml`, `shared-build-and-deploy.yml`) do the module-scoped heavy lifting; five caller workflows (`pr.yml`, `pr-flowvault.yml`, `main.yml`, `release.yml`, `internal-release.yml`) wire up triggers and pass module/version/branch context. Two `ci-scripts/*.sh` scripts do module-aware version read/bump, ported from Java's `scripts/bump_version.sh` and `scripts/current_module_version.sh`.

**Tech Stack:** GitHub Actions (YAML), bash, Python's `setuptools`/`twine`, `coverage.py`, `codecov-action`.

## Global Constraints

- No `common/`, `skyvault/`, `flowvault/` folders or code are created by this plan — see the spec's Non-goal section. Every workflow/script must degrade gracefully (skip with a `::notice::`, not hard-fail the whole job) when a module folder doesn't exist yet, **except** where the spec calls for a hard error (unknown module prefix in a release tag/branch — silently defaulting there risks publishing the wrong package).
- Reuse existing GitHub secret names only: `PAT_ACTIONS`, `PYPI_PUBLISH_TOKEN`, `JFROG_USERNAME`, `JFROG_PASSWORD`, `VALID_SKYFLOW_CREDS_TEST`, `CODECOV_REPO_UPLOAD_TOKEN`. No new secrets.
- `skyvault` publishes as PyPI package `skyflow` (unchanged name). `flowvault` publishes as `skyflow-flowvault-python`. `common` is never published standalone.
- Internal/JFrog releases always publish to the existing repo: `https://prekarilabs.jfrog.io/artifactory/api/pypi/skyflow-python/`.
- Every new/changed `.github/workflows/*.yml` file must parse as valid YAML (`python3 -c "import yaml; yaml.safe_load(open(...))"`) before it's committed.
- Spec: `docs/superpowers/specs/2026-08-27-flowdb-ci-workflows-design.md`. Java reference: `/home/devb/skyflow/skyflow-java/.github/workflows/` and `/home/devb/skyflow/skyflow-java/scripts/`.

---

### Task 1: `ci-scripts/current_module_version.sh`

**Files:**
- Create: `ci-scripts/current_module_version.sh`

**Interfaces:**
- Produces: `current_module_version.sh <module>` → prints `<module>/setup.py`'s `current_version`, with any trailing `.devN+<sha>` suffix stripped, to stdout. Exit 1 with a message on stderr if `<module>/setup.py` doesn't exist or has no `current_version` line. Consumed by Task 4's `shared-build-and-deploy.yml`.

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
# Prints <module>'s own current version from its setup.py, with any existing
# .devN+<sha> suffix stripped. Read-only - never modifies setup.py.
#
# Used by internal releases to get a module's base version without touching
# git tags at all: tags are a flat, repo-wide namespace with no module
# awareness, so a tag-based lookup would risk stamping one module's version
# onto another module's release.
set -euo pipefail

Module="${1:?"Usage: current_module_version.sh <module>"}"
SetupFile="$Module/setup.py"

if [ ! -f "$SetupFile" ]; then
  echo "Error: $SetupFile not found." >&2
  exit 1
fi

version=$(grep -E "current_version = " "$SetupFile" | head -n 1 | sed -E "s/.*current_version = '([^']+)'.*/\1/")

if [ -z "$version" ]; then
  echo "Error: could not find a current_version line in $SetupFile" >&2
  exit 1
fi

# Strip a trailing .devN+<sha> suffix (internal-release versions), if present.
version=$(echo "$version" | sed -E 's/\.dev[0-9]+\+[0-9a-f]+$//')

echo "$version"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x ci-scripts/current_module_version.sh
```

- [ ] **Step 3: Write and run a manual test scenario**

```bash
set -e
TMP="$(mktemp -d)"
mkdir -p "$TMP/skyvault"

# Case 1: plain version
cat > "$TMP/skyvault/setup.py" <<'EOF'
current_version = '1.2.3'
EOF
cd "$TMP"
OUT=$(/home/devb/skyflow/skyflow-python/ci-scripts/current_module_version.sh skyvault)
[ "$OUT" = "1.2.3" ] && echo "PASS: plain version" || { echo "FAIL: got '$OUT'"; exit 1; }

# Case 2: dev-suffixed version gets stripped
cat > "$TMP/skyvault/setup.py" <<'EOF'
current_version = '1.2.3.dev0+abc1234'
EOF
OUT=$(/home/devb/skyflow/skyflow-python/ci-scripts/current_module_version.sh skyvault)
[ "$OUT" = "1.2.3" ] && echo "PASS: dev suffix stripped" || { echo "FAIL: got '$OUT'"; exit 1; }

# Case 3: missing module -> exit 1
if /home/devb/skyflow/skyflow-python/ci-scripts/current_module_version.sh flowvault 2>/dev/null; then
  echo "FAIL: expected non-zero exit for missing module"; exit 1
else
  echo "PASS: missing module exits non-zero"
fi

cd /home/devb/skyflow/skyflow-python
rm -rf "$TMP"
```

Expected output: `PASS: plain version`, `PASS: dev suffix stripped`, `PASS: missing module exits non-zero`.

- [ ] **Step 4: Commit**

```bash
git add ci-scripts/current_module_version.sh
git commit -m "SK-3119: add module-aware current_module_version.sh script

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: `ci-scripts/bump_version.sh` (rewrite, module-aware)

**Files:**
- Modify: `ci-scripts/bump_version.sh` (full rewrite)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `bump_version.sh <version> [<commit-sha>] <module>` → patches `<module>/setup.py`'s `current_version` line, and `<module>/**/_version.py`'s `SDK_VERSION` line if such a file exists (skipped with a notice otherwise). Consumed by Task 4's `shared-build-and-deploy.yml`.

- [ ] **Step 1: Overwrite the script**

```bash
#!/usr/bin/env bash
# Bumps <module>'s version.
#
# Usage: bump_version.sh <version> [<commit-sha>] <module>
#
# Always patches <module>/setup.py's `current_version = '...'` line.
# Also patches a runtime version constant, if this module ships one, found
# at <module>/**/_version.py (matching today's skyflow/utils/_version.py
# convention) - skipped with a notice if no such file exists yet, so this
# script stays correct both before and after modules gain their own runtime
# version file.
set -euo pipefail

Version="${1:?"Usage: bump_version.sh <version> [<commit-sha>] <module>"}"
CommitHash="${2:-}"
Module="${3:?"Usage: bump_version.sh <version> [<commit-sha>] <module>"}"

SetupFile="$Module/setup.py"

if [ ! -f "$SetupFile" ]; then
  echo "Error: $SetupFile not found." >&2
  exit 1
fi

if [ -z "$CommitHash" ]; then
  SEMVER="$Version"
else
  SEMVER="${Version}.dev0+$(echo "$CommitHash" | tr -dc '0-9a-f')"
fi

echo "Bumping $Module version to $SEMVER"

sed -E "s/current_version = .+/current_version = '$SEMVER'/g" "$SetupFile" > tempfile && cat tempfile > "$SetupFile" && rm -f tempfile

version_file=$(find "$Module" -name "_version.py" -print -quit)
if [ -n "$version_file" ]; then
  sed -E "s/SDK_VERSION = .+/SDK_VERSION = '$SEMVER'/g" "$version_file" > tempfile && cat tempfile > "$version_file" && rm -f tempfile
  echo "Also bumped $version_file"
else
  echo "::notice::No _version.py found under $Module yet - skipping runtime version bump"
fi

echo --------------------------
echo "Done, $Module now at $SEMVER"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x ci-scripts/bump_version.sh
```

- [ ] **Step 3: Write and run a manual test scenario**

```bash
set -e
TMP="$(mktemp -d)"
mkdir -p "$TMP/skyvault" "$TMP/flowvault/skyflow_flowvault"

cat > "$TMP/skyvault/setup.py" <<'EOF'
current_version = '1.0.0'
EOF

cat > "$TMP/flowvault/setup.py" <<'EOF'
current_version = '1.0.0'
EOF
cat > "$TMP/flowvault/skyflow_flowvault/_version.py" <<'EOF'
SDK_VERSION = '1.0.0'
EOF

cd "$TMP"

# Case 1: module with no _version.py - only setup.py bumped, notice printed
OUT=$(/home/devb/skyflow/skyflow-python/ci-scripts/bump_version.sh 1.1.0 "" skyvault)
grep -q "current_version = '1.1.0'" skyvault/setup.py && echo "PASS: skyvault setup.py bumped" || { echo "FAIL"; exit 1; }
echo "$OUT" | grep -q "No _version.py found" && echo "PASS: notice printed for skyvault" || { echo "FAIL: no notice"; exit 1; }

# Case 2: module with _version.py - both files bumped
/home/devb/skyflow/skyflow-python/ci-scripts/bump_version.sh 1.1.0 "" flowvault
grep -q "current_version = '1.1.0'" flowvault/setup.py && echo "PASS: flowvault setup.py bumped" || { echo "FAIL"; exit 1; }
grep -q "SDK_VERSION = '1.1.0'" flowvault/skyflow_flowvault/_version.py && echo "PASS: flowvault _version.py bumped" || { echo "FAIL"; exit 1; }

# Case 3: dev-suffixed version (internal release)
/home/devb/skyflow/skyflow-python/ci-scripts/bump_version.sh 1.1.0 abc1234 skyvault
grep -q "current_version = '1.1.0.dev0+abc1234'" skyvault/setup.py && echo "PASS: dev suffix applied" || { echo "FAIL"; exit 1; }

# Case 4: missing module -> exit 1
if /home/devb/skyflow/skyflow-python/ci-scripts/bump_version.sh 1.1.0 "" nonexistent 2>/dev/null; then
  echo "FAIL: expected non-zero exit for missing module"; exit 1
else
  echo "PASS: missing module exits non-zero"
fi

cd /home/devb/skyflow/skyflow-python
rm -rf "$TMP"
```

Expected output: five `PASS:` lines, no `FAIL`.

- [ ] **Step 4: Commit**

```bash
git add ci-scripts/bump_version.sh
git commit -m "SK-3119: make bump_version.sh module-aware

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `.github/workflows/shared-tests.yml` (rewrite)

**Files:**
- Modify: `.github/workflows/shared-tests.yml` (full rewrite)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: reusable workflow callable as `uses: ./.github/workflows/shared-tests.yml` with `inputs.python-version` (string, required) and `secrets: inherit`. Consumed by Task 5 (`pr.yml`) and the pre-existing `main.yml`.

- [ ] **Step 1: Overwrite the file**

```yaml
name: Shared Test Steps

on:
  workflow_call:
    inputs:
      python-version:
        description: 'Python version to use'
        required: true
        type: string

jobs:
  run-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ inputs.python-version }}

      - name: create-json
        id: create-json
        uses: jsdaniell/create-json@1.1.2
        with:
          name: "credentials.json"
          json: ${{ secrets.VALID_SKYFLOW_CREDS_TEST }}

      - name: Install dev dependencies
        run: |
          python -m pip install --upgrade pip
          pip install codespell ruff

      - name: Run Spell Check
        run: codespell

      - name: Run Linter Ruff
        run: ruff check . --output-format=github

      # Each module (common, skyvault, flowvault) is its own installable
      # distribution with its own setup.py and test suite, mirroring Java's
      # per-module Maven build. A module directory that doesn't exist yet
      # (pre-migration) is skipped with a notice rather than failing the job.
      - name: Build, install and test each module
        run: |
          for module in common skyvault flowvault; do
            if [ ! -f "$module/setup.py" ]; then
              echo "::notice::$module/setup.py not found yet - skipping (pre-migration)."
              continue
            fi
            cp credentials.json "$module/credentials.json"
            (
              cd "$module"
              python -m pip install --upgrade pip setuptools wheel
              python setup.py sdist bdist_wheel
              pip install dist/*.whl
              if [ -f requirements.txt ]; then
                pip install -r requirements.txt
              fi
              python -m coverage run --source=. -m unittest discover
              coverage xml -o test-coverage.xml
            )
          done

      - name: Codecov (common)
        if: hashFiles('common/test-coverage.xml') != ''
        uses: codecov/codecov-action@v2.1.0
        with:
          token: ${{ secrets.CODECOV_REPO_UPLOAD_TOKEN }}
          files: common/test-coverage.xml
          flags: common
          name: codecov-skyflow-python-common
          verbose: true

      - name: Codecov (skyvault)
        if: hashFiles('skyvault/test-coverage.xml') != ''
        uses: codecov/codecov-action@v2.1.0
        with:
          token: ${{ secrets.CODECOV_REPO_UPLOAD_TOKEN }}
          files: skyvault/test-coverage.xml
          flags: skyvault
          name: codecov-skyflow-python-skyvault
          verbose: true

      - name: Codecov (flowvault)
        if: hashFiles('flowvault/test-coverage.xml') != ''
        uses: codecov/codecov-action@v2.1.0
        with:
          token: ${{ secrets.CODECOV_REPO_UPLOAD_TOKEN }}
          files: flowvault/test-coverage.xml
          flags: flowvault
          name: codecov-skyflow-python-flowvault
          verbose: true
```

- [ ] **Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/shared-tests.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/shared-tests.yml
git commit -m "SK-3119: rewrite shared-tests.yml to build/test common, skyvault, flowvault

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: `.github/workflows/shared-build-and-deploy.yml` (rewrite)

**Files:**
- Modify: `.github/workflows/shared-build-and-deploy.yml` (full rewrite)

**Interfaces:**
- Consumes: `ci-scripts/current_module_version.sh <module>` (Task 1), `ci-scripts/bump_version.sh <version> [<sha>] <module>` (Task 2).
- Produces: reusable workflow callable as `uses: ./.github/workflows/shared-build-and-deploy.yml` with inputs `ref` (string, required), `tag` (string, required: `internal`|`beta`|`public`), `module` (string, required), `version` (string, optional, default `''`), `release-branch` (string, optional, default `''`), `dry-run` (boolean, optional, default `false`), and `secrets: inherit`. Consumed by Task 7 (`release.yml`) and Task 8 (`internal-release.yml`).

- [ ] **Step 1: Overwrite the file**

```yaml
name: Shared Build and Deploy

on:
  workflow_call:
    inputs:
      ref:
        description: 'Git reference to use (e.g., main or branch name)'
        required: true
        type: string

      tag:
        description: 'Release Tag'
        required: true
        type: string

      module:
        description: 'Module to build and publish (skyvault or flowvault)'
        required: true
        type: string

      version:
        description: >-
          Explicit version to release. Set by tag-triggered (beta/public)
          callers, which parse it out of a <module>/v<semver> tag. When
          empty, the version is derived from the module's own setup.py
          (internal releases).
        required: false
        type: string
        default: ''

      release-branch:
        description: >-
          Branch that receives the version-bump commit, for beta/public
          releases. Supplied by the caller from the GitHub Release's
          target_commitish. A tag records only a commit, never a branch, so
          the branch has to be supplied rather than inferred.
        required: false
        type: string
        default: ''

      dry-run:
        description: >-
          Validate the release pipeline WITHOUT publishing anything.
          Everything still runs - version resolution, the setup.py bump, the
          full build - but 'twine upload' is skipped and the version-bump
          commit is not pushed. Publishing to PyPI is immutable, so this is
          the only safe way to exercise the public path.
        required: false
        type: boolean
        default: false

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0
          ref: ${{ inputs.ref }}
          # Persist an admin credential so the automated version-bump push
          # below satisfies the branch-protection ruleset's repo-admin
          # bypass; the default GITHUB_TOKEN is not a bypass actor.
          token: ${{ secrets.PAT_ACTIONS }}

      - uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install setuptools wheel twine

      - name: Validate release branch input
        if: ${{ inputs.tag == 'beta' || inputs.tag == 'public' }}
        run: |
          if [ -z "${{ inputs.release-branch }}" ]; then
            echo "::error::release-branch is required for ${{ inputs.tag }} releases."
            exit 1
          fi
          # The tagged commit must actually be on that branch, otherwise the
          # bump would land somewhere the release was never cut from.
          if ! git merge-base --is-ancestor HEAD "origin/${{ inputs.release-branch }}"; then
            echo "::error::Tagged commit is not an ancestor of origin/${{ inputs.release-branch }}."
            exit 1
          fi
          echo "Release branch: ${{ inputs.release-branch }}"

      # Version priority: inputs.version (beta/public, parsed from the tag) >
      # the module's own setup.py (internal). Tags are a flat repo-wide
      # namespace with no module awareness, so internal releases read the
      # module's setup.py directly rather than any git-tag lookup - a tag
      # lookup would risk stamping one module's version onto another's build.
      - name: Resolve base version
        id: resolve-version
        run: |
          chmod +x ./ci-scripts/bump_version.sh ./ci-scripts/current_module_version.sh
          if [ -n "${{ inputs.version }}" ]; then
            BASE_VERSION="${{ inputs.version }}"
          else
            BASE_VERSION=$(./ci-scripts/current_module_version.sh "${{ inputs.module }}")
          fi
          echo "base_version=$BASE_VERSION" >> "$GITHUB_OUTPUT"

      - name: Bump Version
        run: |
          if [[ "${{ inputs.tag }}" == "internal" ]]; then
            ./ci-scripts/bump_version.sh "${{ steps.resolve-version.outputs.base_version }}" "$(git rev-parse --short "$GITHUB_SHA")" "${{ inputs.module }}"
          else
            ./ci-scripts/bump_version.sh "${{ steps.resolve-version.outputs.base_version }}" "" "${{ inputs.module }}"
          fi

      - name: Commit changes
        run: |
          git config user.name "${{ github.actor }}"
          git config user.email "${{ github.actor }}@users.noreply.github.com"

          if [[ "${{ inputs.tag }}" == "beta" || "${{ inputs.tag }}" == "public" ]]; then
            git checkout ${{ inputs.release-branch }}
          fi

          git add ${{ inputs.module }}/setup.py

          # Nothing staged = setup.py already at this version. That is
          # success; a bare 'git commit' would exit 1 here.
          if git diff --cached --quiet; then
            echo "::notice::${{ inputs.module }}/setup.py already at the target version - nothing to commit"
            exit 0
          fi

          if [[ "${{ inputs.tag }}" == "internal" ]]; then
            git commit -m "[AUTOMATED] Private Release ${{ steps.resolve-version.outputs.base_version }}.dev0+$(git rev-parse --short $GITHUB_SHA)"
            if [[ "${{ inputs.dry-run }}" == "true" ]]; then
              echo "::notice::DRY RUN - not pushing the version-bump commit"
            else
              git push origin ${{ github.ref_name }} -f
            fi
          fi
          if [[ "${{ inputs.tag }}" == "beta" || "${{ inputs.tag }}" == "public" ]]; then
            git commit -m "[AUTOMATED] Public Release - ${{ steps.resolve-version.outputs.base_version }}"
            if [[ "${{ inputs.dry-run }}" == "true" ]]; then
              echo "::notice::DRY RUN - not pushing the version-bump commit"
            else
              git push origin ${{ inputs.release-branch }}
            fi
          fi

      - name: Build ${{ inputs.module }} package
        run: |
          cd ${{ inputs.module }}
          python setup.py sdist bdist_wheel

      - name: Publish to PyPI
        if: ${{ (inputs.tag == 'beta' || inputs.tag == 'public') && inputs.dry-run != true }}
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_PUBLISH_TOKEN }}
        run: |
          cd ${{ inputs.module }}
          twine upload dist/*

      - name: Publish to JFrog Artifactory
        if: ${{ inputs.tag == 'internal' && inputs.dry-run != true }}
        env:
          TWINE_USERNAME: ${{ secrets.JFROG_USERNAME }}
          TWINE_PASSWORD: ${{ secrets.JFROG_PASSWORD }}
        run: |
          cd ${{ inputs.module }}
          twine upload --repository-url https://prekarilabs.jfrog.io/artifactory/api/pypi/skyflow-python/ dist/*

      - name: Dry run summary
        if: ${{ inputs.dry-run == true }}
        run: echo "::notice::DRY RUN - build completed, nothing was published."
```

- [ ] **Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/shared-build-and-deploy.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/shared-build-and-deploy.yml
git commit -m "SK-3119: rewrite shared-build-and-deploy.yml to be module-scoped

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: `.github/workflows/pr.yml` (replaces `ci.yml`)

**Files:**
- Create: `.github/workflows/pr.yml`
- Delete: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `shared-tests.yml` (Task 3) via `uses: ./.github/workflows/shared-tests.yml`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Create `pr.yml`**

```yaml
name: PR CI Checks

on: [pull_request]

jobs:
  check-commit-message:
    name: Check Commit Message
    runs-on: ubuntu-latest
    steps:
      - name: Check JIRA ID
        uses: gsactions/commit-message-checker@v1
        with:
          pattern: '(\[?[A-Z]{1,5}-[1-9][0-9]*)|(\[AUTOMATED\])|(Merge)|(Release).+$'
          flags: 'gm'
          excludeDescription: 'true'
          checkAllCommitMessages: 'true'
          accessToken: ${{ secrets.PAT_ACTIONS }}
          error: 'One of your your commit messages is not matching the format with JIRA ID Ex: ( SDK-123 commit message )'

  test:
    uses: ./.github/workflows/shared-tests.yml
    with:
      python-version: '3.9'
    secrets: inherit
```

- [ ] **Step 2: Delete `ci.yml`**

```bash
git rm .github/workflows/ci.yml
```

- [ ] **Step 3: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pr.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/pr.yml
git commit -m "SK-3119: rename ci.yml to pr.yml, matching Java's naming

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: `.github/workflows/pr-flowvault.yml` (new)

**Files:**
- Create: `.github/workflows/pr-flowvault.yml`

**Interfaces:**
- Consumes: nothing (inlines its own build/test steps, same as Java's `pr-flowvault.yml`).
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Create the file**

```yaml
name: PR CI Checks (flowvault)

# flowvault is a folder under main, alongside skyvault - not a branch.
# This workflow fires for PRs targeting main or a flowvault-release/* branch
# that actually touch flowvault or its common dependency, and only builds/
# tests those two modules. skyvault (and the full 3-module suite) is covered
# by pr.yml, not here.

on:
  pull_request:
    branches: [ "main", "flowvault-release/**" ]
    paths:
      - "flowvault/**"
      - "common/**"

jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Build flowvault
        run: |
          python -m pip install --upgrade pip setuptools wheel
          cd flowvault
          python setup.py sdist bdist_wheel

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: create-json
        id: create-json
        uses: jsdaniell/create-json@1.1.2
        with:
          name: "credentials.json"
          json: ${{ secrets.VALID_SKYFLOW_CREDS_TEST }}

      - name: Run flowvault unit tests
        run: |
          python -m pip install --upgrade pip setuptools wheel
          cp credentials.json flowvault/credentials.json
          cd flowvault
          python setup.py sdist bdist_wheel
          pip install dist/*.whl
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
          python -m coverage run --source=. -m unittest discover
          coverage xml -o test-coverage.xml

      - name: Codecov
        uses: codecov/codecov-action@v2.1.0
        with:
          token: ${{ secrets.CODECOV_REPO_UPLOAD_TOKEN }}
          files: flowvault/test-coverage.xml
          flags: unittests-flowvault
          name: codecov-skyflow-python-flowvault
          verbose: true
```

- [ ] **Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pr-flowvault.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pr-flowvault.yml
git commit -m "SK-3119: add scoped pr-flowvault.yml, matching Java's fast-path gate

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: `.github/workflows/release.yml` (rewrite for GitHub Release trigger)

**Files:**
- Modify: `.github/workflows/release.yml` (full rewrite)
- Delete: `.github/workflows/beta-release.yml` (merged into `release.yml`)

**Interfaces:**
- Consumes: `shared-build-and-deploy.yml` (Task 4) via `uses: ./.github/workflows/shared-build-and-deploy.yml`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Overwrite `release.yml`**

```yaml
name: Public release

# Triggered by publishing a GitHub Release, not a raw tag push: the Release
# carries both facts needed here - target_commitish (the branch picked in the
# UI; a tag records only a commit) and tag_name (module prefix + version).
#
# Beta and final share this workflow - 'release' events cannot be filtered by
# tag pattern, and both behave identically downstream. Kind comes from the tag.

on:
  release:
    types: [published]

jobs:
  resolve-release:
    runs-on: ubuntu-latest
    outputs:
      module: ${{ steps.parse.outputs.module }}
      version: ${{ steps.parse.outputs.version }}
      kind: ${{ steps.parse.outputs.kind }}
    steps:
      - name: Parse module, version and release kind from the tag
        id: parse
        env:
          TAG: ${{ github.event.release.tag_name }}
          BRANCH: ${{ github.event.release.target_commitish }}
        run: |
          # Expected: <module>/v<semver>[-beta.N]  e.g. flowvault/v1.0.0,
          # skyvault/v2.1.2, flowvault/v1.0.0-beta.1
          if [[ ! "$TAG" =~ ^[a-z]+/v[0-9]+\.[0-9]+\.[0-9]+(-beta\.[0-9]+)?$ ]]; then
            echo "::error::Tag '$TAG' is not <module>/v<semver>[-beta.N]." \
                 "Examples: flowvault/v1.0.0, skyvault/v2.1.2, flowvault/v1.0.0-beta.1"
            exit 1
          fi

          PREFIX="${TAG%%/*}"      # flowvault/v1.0.0 -> flowvault
          VERSION="${TAG#*/}"      # flowvault/v1.0.0 -> v1.0.0
          VERSION="${VERSION#v}"   # v1.0.0           -> 1.0.0

          # Tag prefix -> module directory (both match the directory name).
          case "$PREFIX" in
            flowvault) MODULE="flowvault" ;;
            skyvault)  MODULE="skyvault" ;;
            *)
              echo "::error::Unknown module prefix '$PREFIX' in tag '$TAG'"
              exit 1
              ;;
          esac

          if [[ "$VERSION" == *-beta.* ]]; then KIND="beta"; else KIND="public"; fi

          if [ -z "$BRANCH" ]; then
            echo "::error::Release has no target_commitish - cannot determine the release branch."
            exit 1
          fi

          echo "Tag '$TAG' -> module='$MODULE' version='$VERSION' kind='$KIND' branch='$BRANCH'"
          echo "module=$MODULE"   >> "$GITHUB_OUTPUT"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"
          echo "kind=$KIND"       >> "$GITHUB_OUTPUT"

  build-and-deploy:
    needs: resolve-release
    uses: ./.github/workflows/shared-build-and-deploy.yml
    with:
      ref: ${{ github.event.release.tag_name }}
      tag: ${{ needs.resolve-release.outputs.kind }}
      module: ${{ needs.resolve-release.outputs.module }}
      version: ${{ needs.resolve-release.outputs.version }}
      release-branch: ${{ github.event.release.target_commitish }}
    secrets: inherit
```

- [ ] **Step 2: Delete `beta-release.yml`**

```bash
git rm .github/workflows/beta-release.yml
```

- [ ] **Step 3: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "SK-3119: rewrite release.yml for GitHub Release trigger, drop beta-release.yml

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 8: `.github/workflows/internal-release.yml` (rewrite)

**Files:**
- Modify: `.github/workflows/internal-release.yml` (full rewrite)

**Interfaces:**
- Consumes: `shared-build-and-deploy.yml` (Task 4) via `uses: ./.github/workflows/shared-build-and-deploy.yml`.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Overwrite the file**

```yaml
name: Publish module to the JFrog Artifactory

on:
  push:
    # '**' not '*.*': Actions glob '*' does not match '/', so '*.*' let slash
    # tags (flowvault/v1.0.0) through and fired this branch-only workflow.
    tags-ignore:
      - '**'
    paths-ignore:
      - "*.md"
    branches:
      - flowvault-release/*
      - skyvault-release/*
      # Legacy: predates the per-module naming, still maps to skyvault.
      - release/*

jobs:
  resolve-module:
    runs-on: ubuntu-latest
    # Skip our own bump commit, or this loops: bump -> push -> release -> bump.
    # PAT-authenticated pushes DO trigger workflows; GITHUB_TOKEN pushes do not.
    # build-and-deploy needs this job, so skipping here skips the run.
    if: ${{ !contains(github.event.head_commit.message, '[AUTOMATED]') }}
    outputs:
      module: ${{ steps.set-module.outputs.module }}
    steps:
      # Explicit match, no catch-all: defaulting once published the wrong module.
      - name: Resolve module from branch name
        id: set-module
        env:
          BRANCH: ${{ github.ref_name }}
        run: |
          case "$BRANCH" in
            flowvault-release/*) MODULE="flowvault" ;;
            skyvault-release/*)  MODULE="skyvault" ;;
            release/*)           MODULE="skyvault" ;;
            *)
              echo "::error::Branch '$BRANCH' does not map to a module."
              exit 1
              ;;
          esac
          echo "Branch '$BRANCH' -> module '$MODULE'"
          echo "module=$MODULE" >> "$GITHUB_OUTPUT"

  build-and-deploy:
    needs: resolve-module
    uses: ./.github/workflows/shared-build-and-deploy.yml
    with:
      ref: ${{ github.ref_name }}
      tag: 'internal'
      module: ${{ needs.resolve-module.outputs.module }}
    secrets: inherit
```

- [ ] **Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/internal-release.yml'))" && echo "PASS: valid YAML"
```

Expected: `PASS: valid YAML`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/internal-release.yml
git commit -m "SK-3119: rewrite internal-release.yml to resolve module from branch name

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 9: Final validation and push

**Files:** none created/modified — validation only.

**Interfaces:** none.

- [ ] **Step 1: Confirm `main.yml` already matches the target design (no edit needed)**

```bash
cat .github/workflows/main.yml
```

Expected: it already calls `shared-tests.yml` with `python-version: '3.9'` and `secrets: inherit` — Task 3's rewrite of `shared-tests.yml` is sufficient; `main.yml` itself needs no change.

- [ ] **Step 2: Validate every workflow YAML file in the repo parses**

```bash
for f in .github/workflows/*.yml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" && echo "PASS: $f" || echo "FAIL: $f"
done
```

Expected: `PASS:` for every file, no `FAIL:` lines.

- [ ] **Step 3: List the final workflow directory and diff summary**

```bash
ls .github/workflows/
git log --oneline main..HEAD
git diff --stat main..HEAD
```

Expected: `ci.yml` and `beta-release.yml` are gone; `pr.yml`, `pr-flowvault.yml`, `shared-tests.yml`, `shared-build-and-deploy.yml`, `release.yml`, `internal-release.yml` are present alongside unchanged `main.yml`, `codeql-analysis.yml`, `semgrep.yml`, `pull_request_template.md`.

- [ ] **Step 4: Push the branch**

```bash
git push -u origin devesh/sk-3119
```

Expected: push succeeds, branch `devesh/sk-3119` visible on `origin`.

---

## Self-Review

**Spec coverage:** pr.yml/pr-flowvault.yml (Tasks 5-6) ✓, main.yml (Task 9, confirmed already correct) ✓, release.yml (Task 7) ✓, internal-release.yml (Task 8) ✓, shared-tests.yml (Task 3) ✓, shared-build-and-deploy.yml (Task 4) ✓, bump_version.sh/current_module_version.sh (Tasks 1-2) ✓, non-goal (no folder creation) respected throughout ✓, secret-name reuse ✓, package-naming decisions embedded in `shared-build-and-deploy.yml`'s per-module `setup.py`-driven publish (the actual PyPI package name comes from each module's own `setup.py` once it exists, which is outside this plan's scope) ✓.

**Placeholder scan:** no TBD/TODO; every step has full file content or a runnable command with an expected result.

**Type/interface consistency:** `bump_version.sh <version> [<sha>] <module>` and `current_module_version.sh <module>` signatures match between their definitions (Tasks 1-2) and every call site (Task 4). Reusable-workflow input names (`ref`, `tag`, `module`, `version`, `release-branch`, `dry-run`) match between `shared-build-and-deploy.yml`'s `workflow_call.inputs` (Task 4) and both callers (Tasks 7-8).
