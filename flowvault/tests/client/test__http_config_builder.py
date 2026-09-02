import unittest

from common.errors import SkyflowError
from common.utils.enums import Env
from skyflow_flowvault import Skyflow


def _vault_config(**extra):
    config = {
        "vault_id": "v",
        "cluster_id": "c",
        "env": Env.PROD,
        "credentials": {"api_key": "sky-abcde-" + "f" * 32},
    }
    config.update(extra)
    return config


class TestHttpConfigBuilder(unittest.TestCase):
    def test_methods_store_config(self):
        builder = (
            Skyflow.builder()
            .timeout(30)
            .connect_timeout(5)
            .read_timeout(20)
            .write_timeout(6)
            .max_retries(3)
            .initial_retry_delay_millis(100)
            .max_retry_delay_millis(4000)
        )
        self.assertEqual(builder._client_http_config, {
            "timeout": 30,
            "connect_timeout": 5,
            "read_timeout": 20,
            "write_timeout": 6,
            "max_retries": 3,
            "initial_retry_delay_millis": 100,
            "max_retry_delay_millis": 4000,
        })

    def test_chaining_returns_builder(self):
        builder = Skyflow.builder()
        self.assertIs(builder.timeout(30), builder)
        self.assertIs(builder.max_retries(2), builder)

    def test_invalid_values_raise(self):
        for call in [
            lambda b: b.timeout(-1),
            lambda b: b.connect_timeout(0),
            lambda b: b.read_timeout("x"),
            lambda b: b.max_retries(-1),
            lambda b: b.initial_retry_delay_millis(1.5),
            lambda b: b.max_retry_delay_millis(True),
        ]:
            with self.assertRaises(SkyflowError):
                call(Skyflow.builder())

    def test_client_wide_config_applied_to_vault_client(self):
        client = (
            Skyflow.builder()
            .timeout(33)
            .max_retries(4)
            .add_vault_config(_vault_config())
            .build()
        )
        vault_client = client._get_builder().get_vault_config("v")["vault_client"]
        self.assertEqual(vault_client._common_http_config, {"timeout": 33, "max_retries": 4})
        self.assertEqual(vault_client._resolve("timeout", 60), 33)
        self.assertEqual(vault_client._resolve("max_retries", 0), 4)

    def test_per_vault_overrides_client_wide(self):
        client = (
            Skyflow.builder()
            .timeout(33)
            .add_vault_config(_vault_config(timeout=10))
            .build()
        )
        vault_client = client._get_builder().get_vault_config("v")["vault_client"]
        self.assertEqual(vault_client._resolve("timeout", 60), 10)

    def test_no_client_wide_config_is_empty(self):
        client = Skyflow.builder().add_vault_config(_vault_config()).build()
        vault_client = client._get_builder().get_vault_config("v")["vault_client"]
        self.assertEqual(vault_client._common_http_config, {})


if __name__ == "__main__":
    unittest.main()
