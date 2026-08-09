#!/usr/bin/env bash
# Insert or remove the beta-release disclaimer banner in a README, based on
# whether the given version string is a pre-release build (PEP 440 syntax:
# a pre-release identifier with no separating hyphen, e.g. "2.1.0b1").
#
# Usage: ci-scripts/toggle_beta_banner.sh <readme-path> <version>
#
# Idempotent: safe to run repeatedly against the same file and version.
set -euo pipefail

readme_path="$1"
version="$2"

marker_start="<!-- SKYFLOW-BETA-DISCLAIMER:START -->"
marker_end="<!-- SKYFLOW-BETA-DISCLAIMER:END -->"
banner_body="> ⚠️ **Beta release — not for production use.** This is a pre-release build provided for early testing and feedback. It has not completed Skyflow's General Availability (GA) validation, its API may change before the stable release, and it is not covered by production SLAs or support commitments. Do not deploy beta builds to production environments."

is_prerelease() {
    [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+(a|b|rc)[0-9]+ ]]
}

awk -v start="$marker_start" -v end="$marker_end" '
    { lines[NR] = $0 }
    END {
        start_line = 0
        end_line = 0
        for (i = 1; i <= NR; i++) {
            if (lines[i] == start) start_line = i
            if (lines[i] == end) end_line = i
        }
        if (start_line == 0 || end_line == 0) {
            del_from = -1
            del_to = -1
        } else {
            del_from = start_line
            del_to = end_line
            if (del_from > 1 && lines[del_from - 1] == "") del_from--
            if (del_to < NR && lines[del_to + 1] == "") del_to++
        }
        for (i = 1; i <= NR; i++) {
            if (i >= del_from && i <= del_to) continue
            print lines[i]
        }
    }
' "$readme_path" > "${readme_path}.tmp"
mv "${readme_path}.tmp" "$readme_path"

if is_prerelease "$version"; then
    awk -v start="$marker_start" -v body="$banner_body" -v end="$marker_end" '
        NR == 1 {
            print
            print ""
            print start
            print body
            print end
            print ""
            next
        }
        { print }
    ' "$readme_path" > "${readme_path}.tmp"
    mv "${readme_path}.tmp" "$readme_path"
fi
