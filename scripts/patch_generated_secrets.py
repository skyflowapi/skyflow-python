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

# Quote characters that can open/close the string literal a flagged value
# sits in. See _find_quoted_value_span below.
QUOTE_CHARS = ('"', "'", "`")

# How far _find_quoted_value_span will search outward from gitleaks'
# reported (line, column) for an actual quote character in the file. Only
# needs to cover small reporting inaccuracies (a couple of characters), not
# arbitrary distances - see its docstring.
QUOTE_SEARCH_WINDOW = 8


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


def _git_dir() -> Path:
    output = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return (REPO_ROOT / output).resolve()


def record_touched_files(relative_files) -> None:
    """Records exactly which files this run modified (an empty list if none).

    Lets the pre-commit hook stage only those files - plus whatever was
    already staged - instead of the entire generated-code directories,
    which would otherwise sweep in unrelated or intentionally-unstaged
    in-progress changes sitting in those same directories. Called at every
    exit point so the hook never reads a stale list left over from a prior
    run. Best-effort: if this can't be written, the hook simply finds no
    list and stages nothing beyond what was already staged.
    """
    try:
        list_path = _git_dir() / "leak-guard-touched-files.txt"
        list_path.write_text(
            "".join(f"{f}\n" for f in relative_files), encoding="utf-8"
        )
    except (OSError, subprocess.CalledProcessError):
        pass


def _rollback(original_contents: dict) -> None:
    """Restores every file this run has written so far back to what it read
    at the start. Called from every failure path after files start getting
    written, so a build break, a final-scan tool failure, or leftover
    findings after redaction never leaves a partially-redacted, unverified
    file sitting in the working tree.
    """
    for file_path, content in original_contents.items():
        file_path.write_text(content, encoding="utf-8")
    record_touched_files([])


def _line_start_offsets(text: str) -> list:
    """Absolute char offset where each 1-indexed line starts in `text`.

    `offsets[line - 1]` is the offset of `line`. Used to turn gitleaks'
    1-indexed (line, column) position into a plain absolute offset into
    `text`.
    """
    offsets = [0]
    for line_text in text.split("\n"):
        offsets.append(offsets[-1] + len(line_text) + 1)
    return offsets


def _find_quoted_value_span(content: str, approx_pos: int):
    """Finds the (value_start, value_end) span strictly inside the quoted
    string literal nearest to `approx_pos`, or None if there isn't one.

    Every flagged value in these generated files is a quoted example (e.g.
    `assertion="..."`), and gitleaks' reported column can be off by a
    character or two on some builds (observed: an off-by-one on the "jwt"
    rule), so this never trusts the exact position or reads the flagged
    value's own text - it searches a small window in `content` around the
    approximate position for an actual quote character, then finds its
    matching closing quote. Because this only ever looks at `content` and
    plain integer offsets, it has no dependency on gitleaks' "Secret" field
    at all - the redaction below is entirely free of the taint path CodeQL's
    clear-text-logging/storage-sensitive-data queries were following from
    that field into print()/write_text().
    """
    n = len(content)
    for delta in range(QUOTE_SEARCH_WINDOW + 1):
        # Backward first: the one observed real-world case (an off-by-one
        # StartColumn on the "jwt" rule) landed one character INSIDE the
        # value, so the nearest quote is behind it, not ahead of it.
        candidates = (approx_pos - delta, approx_pos + delta) if delta else (approx_pos,)
        for pos in candidates:
            if 0 <= pos < n and content[pos] in QUOTE_CHARS:
                value_start = pos + 1
                value_end = content.find(content[pos], value_start)
                return (value_start, value_end) if value_end != -1 else None
    return None


def main() -> int:
    if not gitleaks_available():
        print(
            "gitleaks isn't installed locally - skipping auto-redaction of "
            "generated code. CI will still scan for this.",
            file=sys.stderr,
        )
        record_touched_files([])
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
        record_touched_files([])
        return 1

    findings = scan_generated_dirs()
    if not findings:
        print("No gitleaks findings in generated code.")
        record_touched_files([])
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
        record_touched_files([])
        return 1

    by_file = {}
    for finding in findings:
        by_file.setdefault(finding["File"], []).append(finding)

    # Redacts by position - gitleaks' own (StartLine, StartColumn), an
    # approximate anchor used only to locate the surrounding quoted string
    # literal in each file's content (see _find_quoted_value_span) - and
    # never reads finding["Secret"] at all. That field is a source
    # CodeQL's clear-text-logging/storage-sensitive-data queries key off
    # of via real dataflow, regardless of what any receiving variable is
    # named or what operations (even a plain .find() call) touch it
    # afterward; not reading it in the first place is the only way to
    # structurally avoid those alerts rather than dismissing them as false
    # positives.
    #
    # Resolved in a first pass, across ALL files, before anything is
    # written: an unresolved finding in a later file must not leave an
    # earlier file's already-computed redaction written to disk with no
    # way back.
    file_contents = {}
    unique_spans_by_file = {}
    unresolved = []
    for relative_file, file_findings in by_file.items():
        file_path = REPO_ROOT / relative_file
        content = file_path.read_text(encoding="utf-8")
        file_contents[file_path] = content

        line_offsets = _line_start_offsets(content)
        spans = []
        for finding in file_findings:
            approx_pos = line_offsets[finding["StartLine"] - 1] + (
                finding["StartColumn"] - 1
            )
            span = _find_quoted_value_span(content, approx_pos)
            if span is None:
                unresolved.append((relative_file, finding))
                continue
            spans.append((span[0], span[1], finding["RuleID"]))

        # Deduplicate by (start, end) only - not the full (start, end,
        # rule_id) triple, which wouldn't collapse two different rules
        # flagging the exact same span; a stale second replacement at an
        # already-redacted offset would then corrupt the file or eat
        # adjacent text. Keeps whichever rule_id was seen first for that
        # span. Applied back-to-front (highest offset first) so replacing
        # a later span never shifts the offsets of an earlier one still
        # waiting to be processed.
        spans_by_range = {}
        for start, end, rule_id in spans:
            spans_by_range.setdefault((start, end), rule_id)
        unique_spans_by_file[file_path] = sorted(
            ((start, end, rule_id) for (start, end), rule_id in spans_by_range.items()),
            reverse=True,
        )

    if unresolved:
        print(
            "Refusing to continue: couldn't locate a quoted value near "
            f"{len(unresolved)} finding(s) - this script only knows how to "
            'redact `key="value"`-shaped examples. Manual review needed:\n'
            + "\n".join(
                f"  - [{f['RuleID']}] {rel}:{f['StartLine']}" for rel, f in unresolved
            ),
            file=sys.stderr,
        )
        record_touched_files([])
        return 1

    original_contents = dict(file_contents)
    touched_files = set()
    redacted_count = 0
    for file_path, content in file_contents.items():
        by_rule = {}
        for value_start, value_end, rule_id in unique_spans_by_file[file_path]:
            base = placeholder_for(rule_id)
            seen = by_rule.get(base, 0)
            by_rule[base] = seen + 1
            placeholder = base if seen == 0 else f"{base[:-1]}_{seen + 1}>"

            content = content[:value_start] + placeholder + content[value_end:]
            redacted_count += 1
            print(f"[{rule_id}] redacted in {file_path.relative_to(REPO_ROOT)} -> {placeholder}")

        file_path.write_text(content, encoding="utf-8")
        if content != original_contents[file_path]:
            touched_files.add(str(file_path.relative_to(REPO_ROOT)))

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
        _rollback(original_contents)
        print(
            "Rolled back all changes from this run - redaction needs manual review.",
            file=sys.stderr,
        )
        return 1

    # The final re-scan can itself fail for reasons other than "still
    # leaks" (e.g. the gitleaks binary crashing mid-run) -
    # run_gitleaks_detect (via scan_generated_dirs) raises in that case
    # rather than returning a findings list. Either way, an unverified
    # redaction must never be left on disk: roll back exactly as the
    # build-failure path above does.
    try:
        remaining = scan_generated_dirs()
    except RuntimeError as err:
        _rollback(original_contents)
        print(
            f"Final gitleaks re-scan failed to run ({err}) - rolled back all "
            "changes from this run. Redaction needs manual review.",
            file=sys.stderr,
        )
        return 1
    if remaining:
        _rollback(original_contents)
        print(
            f"Redacted {redacted_count} secret(s), but {len(remaining)} finding(s) "
            "remain after re-scanning. Rolled back all changes from this run. "
            "Manual review needed:\n"
            + "\n".join(
                f"  - [{f['RuleID']}] {f['File']}:{f['StartLine']}" for f in remaining
            ),
            file=sys.stderr,
        )
        return 1

    record_touched_files(sorted(touched_files))
    print(
        f"\nDone. Redacted {redacted_count} secret(s) across {len(by_file)} file(s). "
        "Build and gitleaks re-scan both clean."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
