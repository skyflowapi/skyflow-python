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
