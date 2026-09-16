"""Selects the v2 or v3 (flowvault) contract adapter based on SKYFLOW_TEST_VARIANT.
Plain-Python equivalent of a pytest conftest.py fixture -- this repo's test runner is plain
unittest (see each variant's tests/), so variant selection happens via import rather than a
fixture.

Usage (run once per variant, in that variant's own installed/PYTHONPATH environment -- v2's
skyflow and flowvault's skyflow_flowvault can never coexist in one process):

    SKYFLOW_TEST_VARIANT=v2 PYTHONPATH=.:skyvault python -m unittest discover -s tests/contract -t .
    SKYFLOW_TEST_VARIANT=v3 PYTHONPATH=.:flowvault python -m unittest discover -s tests/contract -t .
"""
import os

_VARIANT = os.environ.get("SKYFLOW_TEST_VARIANT")

if _VARIANT == "v2":
    from tests.contract.adapters import v2_adapter as adapter
elif _VARIANT == "v3":
    from tests.contract.adapters import v3_adapter as adapter
else:
    raise RuntimeError(
        "SKYFLOW_TEST_VARIANT must be set to 'v2' or 'v3' before running tests/contract/ "
        "(e.g. SKYFLOW_TEST_VARIANT=v2 PYTHONPATH=.:skyvault python -m unittest discover -s tests/contract -t .)"
    )

VARIANT = _VARIANT
