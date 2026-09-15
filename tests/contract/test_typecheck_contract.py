"""Only meaningful under SKYFLOW_TEST_VARIANT=v3 -- shells out to mypy (or pyright, if mypy
isn't installed) against the fixture and asserts it fails with diagnostics naming each v2-only
field. Skipped entirely under v2 (those kwargs are valid there).

NOT independently verified in this environment: neither mypy nor pyright is installed in the
sandbox this was authored in, so this file has been reviewed for correctness but its actual
pass/fail behavior against a real type checker has not been observed. Install one of them (`pip
install mypy` or `pip install pyright`) before relying on this as a passing gate.
"""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests.contract._adapter_loader import VARIANT

FIXTURE = Path(__file__).parent / "typecheck_fixtures" / "v2_only_insert_kwargs_should_fail_under_v3.py"
V2_ONLY_FIELDS = ["homogeneous", "continue_on_error", "token_mode", "return_tokens"]


@unittest.skipUnless(VARIANT == "v3", "v2-only insert kwargs are valid under v2; nothing to type-check there")
class TestV3RejectsV2OnlyInsertFields(unittest.TestCase):
    def test_v2_only_kwargs_are_flagged_as_type_errors_under_v3(self):
        if shutil.which("mypy") or _module_available("mypy"):
            result = subprocess.run(
                [sys.executable, "-m", "mypy", "--no-error-summary", str(FIXTURE)],
                capture_output=True, text=True,
            )
        elif shutil.which("pyright") or _module_available("pyright"):
            result = subprocess.run(
                [sys.executable, "-m", "pyright", str(FIXTURE)],
                capture_output=True, text=True,
            )
        else:
            self.skipTest("neither mypy nor pyright is installed")
            return

        diagnostics = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, f"expected type errors, got a clean run:\n{diagnostics}")
        for field in V2_ONLY_FIELDS:
            self.assertIn(field, diagnostics, f"expected a diagnostic mentioning '{field}':\n{diagnostics}")


def _module_available(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    unittest.main()
