#!/usr/bin/env bash
# One-time setup: points this clone's git hooks at .githooks (see
# .githooks/pre-commit). Unlike npm's "prepare" script, pip has no
# universal post-install hook to wire this up automatically, so each
# contributor runs this once after cloning:
#   ./scripts/install_git_hooks.sh
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
git -C "$repo_root" config core.hooksPath .githooks
echo "core.hooksPath set to .githooks - the gitleaks pre-commit guard is now active for this clone."
