#!/usr/bin/env bash
#
# Regenerate the committed public-API contract baseline(s) from the CURRENT
# working tree. This is the ONLY sanctioned way a baseline changes.
#
# The baseline is a griffe-derived snapshot of each published package's public
# API surface (an explicit allowlist of modules; see ci-scripts/contract/
# griffe_contract.py). CONTRACT TESTS compare the current surface against the
# committed baseline and fail on any drift. Run this AFTER an intentional public
# API change, review the JSON diff, and commit the refreshed baseline alongside
# the code change so a reviewer sees exactly what contract change was approved.
#
# Only regenerate the module you actually changed.
#
# Usage:
#   ci-scripts/contract-snapshot-update.sh              # both modules
#   ci-scripts/contract-snapshot-update.sh skyvault
#   ci-scripts/contract-snapshot-update.sh flowvault

set -euo pipefail

GRIFFE_VERSION="2.2.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

declare -A PACKAGES=( [skyvault]="skyflow" [flowvault]="skyflow_flowvault" )

modules=("$@")
if [ ${#modules[@]} -eq 0 ]; then
  modules=(skyvault flowvault)
fi

python -m pip install --quiet "griffe==${GRIFFE_VERSION}"

for module in "${modules[@]}"; do
  pkg="${PACKAGES[$module]:-}"
  if [ -z "$pkg" ]; then
    echo "::error::unknown module '$module' (expected skyvault or flowvault)"
    exit 2
  fi
  mkdir -p "$module/api-report"
  python ci-scripts/contract/griffe_contract.py dump "$module" "$module/api-report/${pkg}.api.json"
done

echo "Done. Review the git diff of the api-report/*.api.json file(s) and commit it with your change."
