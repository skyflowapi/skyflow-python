import unittest
from unittest.mock import patch

from common.errors import SkyflowError
from common.utils.enums import Env
from common.utils.constants import SdkMetricsKey
from skyflow.utils import _utils
from skyflow.utils._utils import get_vault_url, get_metrics


class TestGetVaultUrl(unittest.TestCase):
    def test_valid(self):
        url = get_vault_url("cluster123", Env.PROD, "v1")
        self.assertTrue(url.startswith("https://cluster123."))

    def test_invalid_cluster_id_raises(self):
        for bad in ("", "   ", None, 123):
            with self.assertRaises(SkyflowError):
                get_vault_url(bad, Env.PROD, "v1")

    def test_invalid_env_raises(self):
        with self.assertRaises(SkyflowError):
            get_vault_url("cluster123", "not-an-env", "v1")


class _SysPlatformRaises:
    version = "v"

    @property
    def platform(self):
        raise RuntimeError("boom")


class _SysVersionRaises:
    platform = "linux"

    @property
    def version(self):
        raise RuntimeError("boom")


class TestGetMetrics(unittest.TestCase):
    def setUp(self):
        _utils._CACHED_METRICS.clear()

    def tearDown(self):
        _utils._CACHED_METRICS.clear()

    def test_caches_after_first_call(self):
        first = get_metrics()
        self.assertIs(get_metrics(), first)

    def test_device_model_error_falls_back(self):
        with patch.object(_utils.platform, "node", side_effect=RuntimeError("boom")):
            metrics = get_metrics()
        self.assertEqual(metrics[SdkMetricsKey.SDK_CLIENT_DEVICE_MODEL], "")

    def test_os_details_error_falls_back(self):
        with patch.object(_utils, "sys", _SysPlatformRaises()):
            metrics = get_metrics()
        self.assertEqual(metrics[SdkMetricsKey.SDK_CLIENT_OS_DETAILS], "")

    def test_runtime_error_falls_back(self):
        with patch.object(_utils, "sys", _SysVersionRaises()):
            metrics = get_metrics()
        self.assertEqual(metrics[SdkMetricsKey.SDK_RUNTIME_DETAILS], _utils.SdkPrefix.PYTHON_RUNTIME + "")


if __name__ == "__main__":
    unittest.main()
