#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOGGLE="$SCRIPT_DIR/toggle_beta_banner.sh"
FIXTURE="$(mktemp)"
MARKER_START="<!-- SKYFLOW-BETA-DISCLAIMER:START -->"

fail() {
    echo "FAIL: $1"
    rm -f "$FIXTURE"
    exit 1
}

cat > "$FIXTURE" <<'EOF'
# Skyflow Python SDK

Python backend intro text.
EOF

# PEP 440 pre-release version (no hyphen) inserts the banner.
"$TOGGLE" "$FIXTURE" "2.1.0b1"
[ "$(grep -c -F "$MARKER_START" "$FIXTURE")" -eq 1 ] || fail "banner not inserted for beta version"

"$TOGGLE" "$FIXTURE" "2.1.0b1"
[ "$(grep -c -F "$MARKER_START" "$FIXTURE")" -eq 1 ] || fail "banner duplicated on repeat run"

"$TOGGLE" "$FIXTURE" "2.1.0"
[ "$(grep -c -F "$MARKER_START" "$FIXTURE")" -eq 0 ] || fail "banner not removed for GA version"

grep -qF "intro text." "$FIXTURE" || fail "original README content lost"

rm -f "$FIXTURE"
echo "PASS: toggle_beta_banner.sh"
