#!/usr/bin/env python3
"""
Monthly dependency audit — compares each dep's floor version across
requirements.txt and setup.py against the latest version on PyPI and
prints a markdown report. Exits 1 if any outdated deps are found so
CI can detect and open a GitHub Issue.

Usage:
    python ci-scripts/audit_deps.py [file1 file2 ...]
    python ci-scripts/audit_deps.py requirements.txt setup.py
"""
import json
import re
import sys
import urllib.request

PYPI_URL = "https://pypi.org/pypi/{package}/json"
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
        key = name.lower().replace("-", "_")
        if key not in deps:
            deps[key] = (name, version)
    return deps


def get_latest_version(package):
    url = PYPI_URL.format(package=package)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data["info"]["version"], None
    except Exception as e:
        return None, str(e)


def version_tuple(v):
    return tuple(int(x) for x in v.split(".")[:3] if x.isdigit())


def main():
    files = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

    deps = {}
    for f in files:
        deps.update(parse_deps(f))

    outdated, up_to_date, errors = [], [], []

    for _, (package, floor) in sorted(deps.items()):
        latest, error = get_latest_version(package)
        if error or not latest:
            errors.append((package, floor, error))
            continue
        if version_tuple(latest) > version_tuple(floor):
            outdated.append((package, floor, latest))
        else:
            up_to_date.append((package, floor, latest))

    print("## Monthly Dependency Audit\n")

    if outdated:
        print(f"### ⚠️ {len(outdated)} outdated dep(s) — review and bump after thorough testing\n")
        print("| Package | Current Floor | Latest on PyPI |")
        print("|---|---|---|")
        for pkg, cur, lat in outdated:
            print(f"| `{pkg}` | `{cur}` | `{lat}` |")
        print()

    if up_to_date:
        print(f"### ✅ {len(up_to_date)} up to date\n")
        print("| Package | Current Floor | Latest on PyPI |")
        print("|---|---|---|")
        for pkg, cur, lat in up_to_date:
            print(f"| `{pkg}` | `{cur}` | `{lat}` |")
        print()

    if errors:
        print("### ⚠️ Could not check\n")
        for pkg, cur, err in errors:
            print(f"- `{pkg}` ({cur}): {err}")
        print()

    print("> Bump versions in both `requirements.txt` and `setup.py` after testing.")
    print("> The 14-day stability gate in CI will block any version newer than 14 days.")

    sys.exit(1 if outdated else 0)


if __name__ == "__main__":
    main()
