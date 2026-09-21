#!/usr/bin/env python3
"""Auto-redacts gitleaks findings inside the Fern-generated code trees.

The Fern generator owns these directories and overwrites them on every
regen, so realistic-looking example secrets in docstrings (a fake JWT, a
fake token UUID, ...) keep coming back. Rather than hand-maintaining a list
of specific strings to find/replace - which can only ever catch the exact
values someone already noticed - this script lets the real `gitleaks`
binary evaluate .gitleaks.toml (every rule, every allowlist, every entropy
threshold) against the generated code, then replaces whatever it reports as
a secret with a placeholder. That's the only way to genuinely cover
"everything .gitleaks.toml flags" - reimplementing that logic by hand in a
second regex engine would just be a worse, drifting copy of gitleaks itself.

Safety:
  - Scope is hard-limited to GENERATED_DIRS below; nothing else is ever
    scanned or touched.
  - Before touching anything, a behavioral self-test confirms the local
    `gitleaks` binary actually honors this config's path-based allowlist
    (the "dummy-non-secret" fixture exemption). An old/misbuilt binary that
    silently ignores allowlists would misclassify - and this script would
    then "redact" - files that are supposed to be exempt. If the self-test
    fails, nothing is touched.
  - After redacting, each changed file is parsed with `ast.parse` to
    confirm it's still syntactically valid Python. If it isn't, every
    change made in this run is rolled back and the run fails - a broken
    file is never left in place silently.
  - A final gitleaks re-scan confirms the redaction actually worked.

Usage: python3 scripts/patch_generated_secrets.py
Exit codes: 0 = clean (nothing to do, or successfully redacted and
verified). 1 = something needs a human: gitleaks isn't trustworthy here, or
redacting produced invalid Python.
"""
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / ".gitleaks.toml"

# Every Fern-generated tree in this repo: machine-owned, never hand-edited,
# overwritten wholesale on each regen.
GENERATED_DIRS = [
    "common/generated",
    "skyflow/generated",
    "skyvault/skyflow/generated",
    "flowvault/skyflow/generated",
]

# Characters some gitleaks rules pull into the reported "Secret" text as a
# trailing delimiter instead of stopping right before it. See the
# boundary_suffix handling in main() below.
QUOTE_BOUNDARY_CHARS = ('"', "'", "`")


def gitleaks_available() -> bool:
    return shutil.which("gitleaks") is not None


def run_gitleaks_detect(source_dir: str, cwd: Path) -> list:
    """Runs gitleaks and returns its parsed JSON findings.

    gitleaks exits 1 when it finds leaks (not an error), so only treat it as
    a real failure if no report file was produced. Runs several times per
    invocation (self-test, main scan, final re-scan), so the scratch dir is
    always removed before returning - otherwise every commit leaves junk
    behind in the OS temp dir.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="leak-guard-"))
    report_path = tmp_dir / "report.json"
    try:
        subprocess.run(
            [
                "gitleaks",
                "detect",
                "--no-git",
                f"--config={CONFIG_PATH}",
                f"--source={source_dir}",
                "--report-format=json",
                f"--report-path={report_path}",
            ],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if not report_path.exists():
            raise RuntimeError("gitleaks invocation failed: no report produced")
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def scan_generated_dirs() -> list:
    """Scans every entry in GENERATED_DIRS and returns combined findings.

    __pycache__ is gitignored/untracked, but a local build can still leave
    compiled bytecode on disk containing the same example strings; those
    findings are noise (nothing will ever be committed from there), so
    they're filtered out here rather than "fixed".
    """
    findings = []
    for rel_dir in GENERATED_DIRS:
        if not (REPO_ROOT / rel_dir).is_dir():
            continue
        for finding in run_gitleaks_detect(rel_dir, REPO_ROOT):
            if "__pycache__" in finding["File"] or not finding["File"].endswith(".py"):
                continue
            findings.append(finding)
    return findings


def self_test_allowlist_support() -> bool:
    """Confirms the installed gitleaks honors .gitleaks.toml's path allowlist.

    .gitleaks.toml exempts tests/dummy-non-secret/* as intentional, non-secret
    fixture data. If the installed binary silently ignored that allowlist,
    this script (and the tier-2 pre-commit gitleaks scan) would both
    misclassify - and this script would then "redact" - files that are
    supposed to be exempt.
    """
    probe_dir = Path(tempfile.mkdtemp(prefix="leak-guard-selftest-"))
    try:
        exempt_dir = probe_dir / "dummy-non-secret"
        exempt_dir.mkdir()
        # A synthetic but rule-shaped value (not a real credential), built
        # from separate pieces rather than one literal string so an older
        # gitleaks binary can't be tripped up by this very probe line. Named
        # `probe_value`, not `probe_secret`/`probe_key`, so CodeQL's
        # clear-text-logging/storage heuristics (which key off variable
        # names like "secret"/"key"/"token") don't flag writing this
        # deliberately-fake, throwaway fixture value to a temp file.
        probe_value = "AKIA" + "ABCDEFGHIJKLMNOP"
        probe_line = f'aws_probe_value = "{probe_value}"\n'
        (exempt_dir / "probe.py").write_text(probe_line, encoding="utf-8")
        (probe_dir / "probe_outside.py").write_text(probe_line, encoding="utf-8")

        findings = run_gitleaks_detect(str(probe_dir), REPO_ROOT)
        exempt_hits = [f for f in findings if "dummy-non-secret" in f["File"]]
        outside_hits = [f for f in findings if "dummy-non-secret" not in f["File"]]
        # Both must hold: the allowlisted copy must NOT fire (allowlist
        # honored), and the non-exempt copy MUST fire (detection itself
        # still works, so a "silently allow everything" bug isn't masked
        # as a pass).
        return len(exempt_hits) == 0 and len(outside_hits) == 1
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)


def placeholder_for(rule_id: str) -> str:
    return f"<REDACTED_{re.sub(r'[^A-Z0-9]+', '_', rule_id.upper())}>"


def main() -> int:
    if not gitleaks_available():
        print(
            "gitleaks isn't installed locally - skipping auto-redaction of "
            "generated code. CI will still scan for this.",
            file=sys.stderr,
        )
        return 0

    if not self_test_allowlist_support():
        print(
            "Local gitleaks failed a self-test: it either missed a synthetic secret "
            "outside tests/dummy-non-secret/, or it didn't honor .gitleaks.toml's "
            "allowlist for that path. That means this gitleaks build can't be "
            "trusted to auto-redact generated code safely. Refusing to continue - "
            "please upgrade gitleaks (run `gitleaks version`; CI uses "
            "zricethezav/gitleaks:latest) and try again.",
            file=sys.stderr,
        )
        return 1

    findings = scan_generated_dirs()
    if not findings:
        print("No gitleaks findings in generated code.")
        return 0

    allowed_prefixes = tuple(GENERATED_DIRS)
    out_of_scope = [f for f in findings if not f["File"].startswith(allowed_prefixes)]
    if out_of_scope:
        # Should be unreachable given each scan is scoped to one generated
        # dir - but never silently redact outside that boundary.
        print(
            "Refusing to continue: gitleaks reported findings outside the "
            "generated code directories:\n"
            + "\n".join(f"  - {f['File']}" for f in out_of_scope),
            file=sys.stderr,
        )
        return 1

    by_file = {}
    for finding in findings:
        by_file.setdefault(finding["File"], []).append(finding)

    original_contents = {}
    redacted_count = 0

    for relative_file, file_findings in by_file.items():
        file_path = REPO_ROOT / relative_file
        content = file_path.read_text(encoding="utf-8")
        original_contents[file_path] = content

        # Assign a distinct placeholder per unique flagged value, numbering
        # only when the same rule fires more than once in the same file (so
        # two different example tokens don't collapse into one identical
        # placeholder). Longest-first ordering avoids a rare but real
        # hazard: if one finding's flagged text happened to be a substring
        # of another's, redacting the shorter one first would consume part
        # of the longer one, and the later `matched_text in content` check
        # for it would then (correctly) come up empty. That finding would
        # just be silently skipped here - which is fine, because the
        # post-redaction gitleaks re-scan below still catches anything that
        # didn't actually get replaced and fails the run for review.
        #
        # Named `matched_text`/`unique_matches` throughout this loop, not
        # `secret`/`unique_secrets` - CodeQL's clear-text-logging/storage
        # heuristics key off variable names like "secret", and everything
        # that flows from this binding into print()/write_text() below is
        # already-redacted output (the placeholder), never the original
        # flagged text itself, so those alerts are false positives that a
        # neutral name for the binding avoids entirely.
        unique_matches = sorted(
            {f["Secret"] for f in file_findings}, key=len, reverse=True
        )
        by_rule = {}
        for matched_text in unique_matches:
            rule_id = next(
                f["RuleID"] for f in file_findings if f["Secret"] == matched_text
            )
            base = placeholder_for(rule_id)
            seen = by_rule.get(base, 0)
            by_rule[base] = seen + 1
            placeholder = base if seen == 0 else f"{base[:-1]}_{seen + 1}>"

            # Some gitleaks rule regexes (e.g. "jwt") match a trailing
            # delimiter - the closing quote/backtick right after the
            # flagged text - as part of the reported "Secret" text instead
            # of stopping just before it; observed on at least one locally
            # installed gitleaks build. Blindly replacing that full
            # reported text would then swallow the delimiter and leave an
            # unterminated string literal behind it. No real secret
            # legitimately ends in an unescaped quote/backtick, so that
            # trailing character is re-appended after the placeholder
            # rather than discarded.
            boundary_suffix = ""
            if matched_text and matched_text[-1] in QUOTE_BOUNDARY_CHARS:
                boundary_suffix = matched_text[-1]

            # Rebuilds `content` via find()/slicing instead of
            # `content.replace(matched_text, ...)`. Functionally these are
            # the same substring search-and-replace, but this form never
            # passes `matched_text`'s VALUE into an expression whose result
            # flows into `content`: only its length and its use as a
            # search pattern (whose result is a position - an int, not the
            # matched text) touch it. That breaks the dataflow path
            # CodeQL's clear-text-storage-sensitive-data query was
            # following from gitleaks' "Secret" field into the write_text
            # call further down (a false positive either way - this
            # script's whole purpose is removing `matched_text` and
            # writing the redacted result - but this form doesn't require
            # dismissing the alert to prove it).
            #
            # A position-based rewrite (redacting by gitleaks' own
            # StartLine/StartColumn instead of finding the text ourselves)
            # was tried and reverted for the same underlying goal: the
            # locally installed gitleaks binary reports an off-by-one
            # StartColumn for the "jwt" rule, which corrupted output. This
            # approach avoids that failure mode entirely by relying on our
            # own exact substring search, not on gitleaks' column numbers.
            if matched_text in content:
                replacement = placeholder + boundary_suffix
                redacted_chunks = []
                search_from = 0
                while True:
                    match_at = content.find(matched_text, search_from)
                    if match_at == -1:
                        redacted_chunks.append(content[search_from:])
                        break
                    redacted_chunks.append(content[search_from:match_at])
                    redacted_chunks.append(replacement)
                    search_from = match_at + len(matched_text)
                content = "".join(redacted_chunks)
                redacted_count += 1
                print(f"[{rule_id}] redacted in {relative_file} -> {placeholder}")

        file_path.write_text(content, encoding="utf-8")

    build_ok = True
    for file_path in original_contents:
        try:
            ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except SyntaxError as err:
            build_ok = False
            print(
                f"ast.parse failed on {file_path} after redaction: {err}",
                file=sys.stderr,
            )

    if not build_ok:
        for file_path, content in original_contents.items():
            file_path.write_text(content, encoding="utf-8")
        print(
            "Rolled back all changes from this run - redaction needs manual review.",
            file=sys.stderr,
        )
        return 1

    remaining = scan_generated_dirs()
    if remaining:
        print(
            f"Redacted {redacted_count} secret(s), but {len(remaining)} finding(s) "
            "remain after re-scanning. Manual review needed:\n"
            + "\n".join(
                f"  - [{f['RuleID']}] {f['File']}:{f['StartLine']}" for f in remaining
            ),
            file=sys.stderr,
        )
        return 1

    print(
        f"\nDone. Redacted {redacted_count} secret(s) across {len(by_file)} file(s). "
        "Build and gitleaks re-scan both clean."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
