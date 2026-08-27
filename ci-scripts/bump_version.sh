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
