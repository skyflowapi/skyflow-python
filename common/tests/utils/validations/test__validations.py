import unittest

from common.errors import SkyflowError
from common.utils import SkyflowMessages, LogLevel, Env
from common.utils.validations import (
    validate_vault_config,
    validate_update_vault_config,
    validate_credentials,
    validate_log_level,
    validate_non_empty_string_list,
)

VALID_VAULT_CONFIG = {
    "vault_id": "vault123",
    "cluster_id": "cluster1",
    "env": Env.PROD,
    "credentials": {"api_key": "sky-abcde-" + "f" * 32},
}


class FakeMessages:
    """Stand-in message catalog to confirm validate_vault_config/etc. actually use the
    `messages` param passed in, rather than silently falling back to common's own."""

    class Error:
        class _M:
            def __init__(self, text):
                self._text = text

            @property
            def value(self):
                return self._text

            def format(self, *args, **kwargs):
                return self._text

        EMPTY_VAULT_ID = _M("FAKE: empty vault id")
        INVALID_VAULT_ID = _M("FAKE: invalid vault id")
        EMPTY_CLUSTER_ID = _M("FAKE: empty cluster id")
        INVALID_CLUSTER_ID = _M("FAKE: invalid cluster id")
        EMPTY_CREDENTIALS = _M("FAKE: empty credentials")
        INVALID_ENV = _M("FAKE: invalid env")
        INVALID_KEY = _M("FAKE: invalid key")
        INVALID_LOG_LEVEL = _M("FAKE: invalid log level")
        INVALID_CREDENTIALS = _M("FAKE: invalid credentials")
        INVALID_CREDENTIALS_IN_CONFIG = _M("FAKE: invalid credentials in config")

    class ErrorLogs:
        class _M:
            def __init__(self, text):
                self._text = text

            @property
            def value(self):
                return self._text

        VAULTID_IS_REQUIRED = _M("fake log")
        CLUSTER_ID_IS_REQUIRED = _M("fake log")
        CONNECTION_ID_IS_REQUIRED = _M("fake log")
        INVALID_CONNECTION_URL = _M("fake log")
        EMPTY_VAULTID = _M("fake log")
        EMPTY_CLUSTER_ID = _M("fake log")
        EMPTY_CONNECTION_ID = _M("fake log")
        EMPTY_CONNECTION_URL = _M("fake log")
        EMPTY_CREDENTIALS_PATH = _M("fake log")
        EMPTY_CREDENTIALS_STRING = _M("fake log")
        EMPTY_TOKEN_VALUE = _M("fake log")
        EMPTY_API_KEY_VALUE = _M("fake log")
        INVALID_KEY = _M("fake log")
        INVALID_LOG_LEVEL = _M("fake log")
        ENV_IS_REQUIRED = _M("fake log")

    class Info:
        class _M:
            def __init__(self, text):
                self._text = text

            @property
            def value(self):
                return self._text

        VALIDATING_VAULT_CONFIG = _M("fake info")


class TestValidateVaultConfig(unittest.TestCase):
    def test_valid_config_passes(self):
        self.assertTrue(validate_vault_config(None, dict(VALID_VAULT_CONFIG)))

    def test_missing_vault_id_raises(self):
        config = dict(VALID_VAULT_CONFIG)
        del config["vault_id"]
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, config)

    def test_unknown_key_raises(self):
        config = dict(VALID_VAULT_CONFIG)
        config["unexpected"] = True
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, config)

    def test_empty_credentials_raises(self):
        config = dict(VALID_VAULT_CONFIG)
        config["credentials"] = {}
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, config)

    def test_credentials_are_validated(self):
        config = dict(VALID_VAULT_CONFIG)
        config["credentials"] = {"api_key": "not-a-valid-key"}
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, config)

    def test_uses_injected_messages_for_raised_error(self):
        config = dict(VALID_VAULT_CONFIG)
        del config["vault_id"]
        with self.assertRaises(SkyflowError) as ctx:
            validate_vault_config(None, config, messages=FakeMessages)
        self.assertIn("FAKE", ctx.exception.message)

    def test_defaults_to_common_messages_when_not_injected(self):
        config = dict(VALID_VAULT_CONFIG)
        del config["vault_id"]
        with self.assertRaises(SkyflowError) as ctx:
            validate_vault_config(None, config)
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.INVALID_VAULT_ID.value)


class TestValidateUpdateVaultConfig(unittest.TestCase):
    def test_valid_update_passes(self):
        self.assertTrue(validate_update_vault_config(None, dict(VALID_VAULT_CONFIG)))

    def test_credentials_required_on_update(self):
        """Unlike validate_vault_config, credentials are mandatory here."""
        config = dict(VALID_VAULT_CONFIG)
        del config["credentials"]
        with self.assertRaises(SkyflowError):
            validate_update_vault_config(None, config)

    def test_uses_injected_messages(self):
        config = dict(VALID_VAULT_CONFIG)
        del config["credentials"]
        with self.assertRaises(SkyflowError) as ctx:
            validate_update_vault_config(None, config, messages=FakeMessages)
        self.assertIn("FAKE", ctx.exception.message)


class TestValidateCredentialsMessageInjection(unittest.TestCase):
    def test_uses_injected_messages(self):
        with self.assertRaises(SkyflowError) as ctx:
            validate_credentials(None, {}, messages=FakeMessages)
        self.assertIn("FAKE", ctx.exception.message)

    def test_defaults_to_common_messages(self):
        with self.assertRaises(SkyflowError) as ctx:
            validate_credentials(None, {})
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS.value)


class TestValidateLogLevelMessageInjection(unittest.TestCase):
    def test_valid_log_level_passes(self):
        validate_log_level(None, LogLevel.INFO)  # should not raise

    def test_uses_injected_messages(self):
        with self.assertRaises(SkyflowError) as ctx:
            validate_log_level(None, "not-a-log-level", messages=FakeMessages)
        self.assertIn("FAKE", ctx.exception.message)


class TestValidateNonEmptyStringList(unittest.TestCase):
    def test_valid_list_passes(self):
        validate_non_empty_string_list(None, ["a", "b"], "boom")  # should not raise

    def test_non_list_raises_with_given_error(self):
        with self.assertRaises(SkyflowError) as ctx:
            validate_non_empty_string_list(None, "not-a-list", "boom")
        self.assertEqual(ctx.exception.message, "boom")

    def test_empty_list_raises(self):
        with self.assertRaises(SkyflowError):
            validate_non_empty_string_list(None, [], "boom")

    def test_none_raises(self):
        with self.assertRaises(SkyflowError):
            validate_non_empty_string_list(None, None, "boom")

    def test_non_string_entry_raises(self):
        with self.assertRaises(SkyflowError):
            validate_non_empty_string_list(None, ["a", 1], "boom")

    def test_blank_string_entry_raises(self):
        with self.assertRaises(SkyflowError):
            validate_non_empty_string_list(None, ["a", "  "], "boom")


if __name__ == "__main__":
    unittest.main()
