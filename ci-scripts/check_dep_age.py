#!/usr/bin/env python3
"""
Verify all dependencies in requirements.txt and setup.py were released
at least STABILITY_DAYS ago on PyPI. Blocks newly published versions from
being used before the community has had time to flag vulnerabilities.

Usage:
    python ci-scripts/check_dep_age.py [file1 file2 ...]
    python ci-scripts/check_dep_age.py requirements.txt setup.py
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

STABILITY_DAYS = 14
PYPI_JSON_URL = "https://pypi.org/pypi/{package}/{version}/json"
DEFAULT_FILES = ["requirements.txt", "setup.py"]


def parse_deps(filepath):
    deps = {}
    with open(filepath) as f:
        content = f.read()
    for match in re.finditer(
        r"([a-zA-Z0-9][a-zA-Z0-9._-]*)\s*(?:>=|~=|==|<=)\s*([0-9][0-9.]*)",
        content,
    ):
        name, version = match.group(1), match.group(2)
        # normalise name so PyJWT and pyjwt are treated as the same key
        key = name.lower().replace("-", "_")
        if key not in deps:
            deps[key] = (name, version)
    return deps


def get_release_age_days(package, version):
    url = PYPI_JSON_URL.format(package=package, version=version)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        urls = data.get("urls", [])
        if not urls:
            return None, f"{package} {version} not found on PyPI"
        upload_time = urls[0]["upload_time"]
        release_date = datetime.fromisoformat(upload_time).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - release_date).days
        return age_days, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, f"{package} {version} not found on PyPI (404) — version may not exist yet"
        return None, f"HTTP {e.code} fetching {package} {version}"
    except Exception as e:
        return None, f"Error checking {package} {version}: {e}"


def main():
    files = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

    deps = {}
    for f in files:
        deps.update(parse_deps(f))

    if not deps:
        print("No dependencies found.")
        sys.exit(0)

    failed = []
    warnings = []

    for _, (package, version) in sorted(deps.items()):
        age, error = get_release_age_days(package, version)
        if error:
            warnings.append(f"⚠️  {error}")
            continue
        if age < STABILITY_DAYS:
            failed.append((package, version, age))
            print(f"❌ {package} {version} — released {age} day(s) ago (minimum {STABILITY_DAYS} days required)")
        else:
            print(f"✅ {package} {version} — {age} days old")

    for w in warnings:
        print(w)

    if failed:
        print(f"\n{len(failed)} dep(s) do not meet the {STABILITY_DAYS}-day stability freeze.")
        sys.exit(1)

    print(f"\nAll dependencies meet the {STABILITY_DAYS}-day stability requirement.")
    sys.exit(0)


if __name__ == "__main__":
    main()
