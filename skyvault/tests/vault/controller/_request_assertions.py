"""Shared assertions for what the controllers actually send to the generated REST client.

The controller tests mock the API layer, so `assert_called_once()` on its own only proves the
controller reached the API — never that it built the right request. These helpers close that
gap: a wrong table name, a dropped field or a flipped flag has to fail a test.
"""
import json

from skyflow.utils._version import SDK_VERSION
from skyflow.utils.constants import SKY_META_DATA_HEADER, SdkMetricsKey, SdkPrefix

# Identical on every call, and covered once by assert_sky_metadata instead of in every test.
IGNORED_KWARGS = ("request_options",)


def assert_request(test_case, api_mock, expected_kwargs, expected_args=None):
    """Assert api_mock was called exactly once, with exactly this request.

    Compares the whole kwargs dict rather than a subset, so a dropped or renamed parameter
    fails too - not just a wrong value.
    """
    api_mock.assert_called_once()
    args, kwargs = api_mock.call_args
    if expected_args is not None:
        test_case.assertEqual(args, expected_args)
    actual_kwargs = {key: value for key, value in kwargs.items() if key not in IGNORED_KWARGS}
    test_case.assertEqual(actual_kwargs, expected_kwargs)


def assert_sky_metadata(test_case, additional_headers):
    """Assert a sky-metadata header is present and names this SDK version."""
    test_case.assertIn(SKY_META_DATA_HEADER, additional_headers)
    metrics = json.loads(additional_headers[SKY_META_DATA_HEADER])
    test_case.assertEqual(
        metrics[SdkMetricsKey.SDK_NAME_VERSION],
        SdkPrefix.SKYFLOW_PYTHON + SDK_VERSION
    )


def request_options_headers(api_mock):
    """The additional_headers the controller passed in request_options."""
    _, kwargs = api_mock.call_args
    return kwargs["request_options"]["additional_headers"]
