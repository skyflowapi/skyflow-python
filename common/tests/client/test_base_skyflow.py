import unittest

from common.errors import SkyflowError
from common.utils import LogLevel, SkyflowMessages
from common.utils.logger import Logger
from common.client.base_skyflow import BaseSkyflow, make_skyflow_class


class FakeVaultClient:
    def __init__(self, config):
        self._config = dict(config)
        self.credentials = None
        self.logger = None

    def get_config(self):
        return self._config

    def update_config(self, config):
        self._config.update(config)

    def set_logger(self, log_level, logger):
        self.logger = logger

    def set_common_skyflow_credentials(self, credentials):
        self.credentials = credentials


class FakeVaultController:
    def __init__(self, vault_client):
        self.vault_client = vault_client


class FakeConnection:
    def __init__(self, vault_client):
        self.vault_client = vault_client


class FakeDetect:
    def __init__(self, vault_client):
        self.vault_client = vault_client


def _noop_validate(logger, config):
    return True


def make_fake_skyflow(with_connections=False, with_detect=False):
    kwargs = dict(
        vault_client_cls=FakeVaultClient,
        vault_controller_cls=FakeVaultController,
        logger_cls=Logger,
        default_log_level=LogLevel.ERROR,
        skyflow_messages=SkyflowMessages,
        validate_vault_config=_noop_validate,
        validate_update_vault_config=_noop_validate,
        validate_log_level=_noop_validate,
        validate_credentials=_noop_validate,
    )
    if with_connections:
        kwargs.update(
            connection_cls=FakeConnection,
            validate_connection_config=_noop_validate,
            validate_update_connection_config=_noop_validate,
        )
    if with_detect:
        kwargs['detect_cls'] = FakeDetect
    return make_skyflow_class(**kwargs)


VAULT_CONFIG = {"vault_id": "v1", "cluster_id": "c1", "credentials": {"token": "t"}}


class TestMakeSkyflowClassBasics(unittest.TestCase):
    def test_build_returns_instance_of_the_produced_class_not_the_template(self):
        """Regression pin: build()/builder() must resolve to the specific class produced by
        make_skyflow_class(), not the shared template -- two variants must never collide."""
        SkyflowA = make_fake_skyflow()
        SkyflowB = make_fake_skyflow()
        client_a = SkyflowA.builder().add_vault_config(VAULT_CONFIG).build()
        self.assertIsInstance(client_a, SkyflowA)
        self.assertNotIsInstance(client_a, SkyflowB)

    def test_two_produced_classes_do_not_share_hooks(self):
        SkyflowWithDetect = make_fake_skyflow(with_detect=True)
        SkyflowWithoutDetect = make_fake_skyflow(with_detect=False)
        self.assertIsNotNone(SkyflowWithDetect.Builder._detect_cls)
        self.assertIsNone(SkyflowWithoutDetect.Builder._detect_cls)

    def test_vault_config_crud(self):
        Skyflow = make_fake_skyflow()
        builder = Skyflow.builder()
        builder.add_vault_config(VAULT_CONFIG)
        client = builder.build()

        vault_config = client.get_vault_config("v1")
        self.assertEqual(vault_config.get("vault_id"), "v1")

        updated = dict(VAULT_CONFIG)
        updated["cluster_id"] = "c2"
        client.update_vault_config(updated)
        self.assertEqual(client.get_vault_config("v1").get("cluster_id"), "c2")

        client.remove_vault_config("v1")
        with self.assertRaises(SkyflowError):
            client.get_vault_config("v1")

    def test_vault_returns_the_controller(self):
        Skyflow = make_fake_skyflow()
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        self.assertIsInstance(client.vault("v1"), FakeVaultController)

    def test_add_skyflow_credentials_and_update(self):
        Skyflow = make_fake_skyflow()
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        client.add_skyflow_credentials({"token": "a"})
        client.update_skyflow_credentials({"token": "b"})
        # no assertion error means both delegate correctly to the same underlying builder path

    def test_set_get_and_deprecated_update_log_level(self):
        Skyflow = make_fake_skyflow()
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        client.set_log_level(LogLevel.INFO)
        self.assertEqual(client.get_log_level(), LogLevel.INFO)

        client.update_log_level(LogLevel.WARN)
        self.assertEqual(client.get_log_level(), LogLevel.WARN)


class TestConnectionAndDetectGating(unittest.TestCase):
    def test_connection_methods_raise_when_connection_cls_not_supplied(self):
        Skyflow = make_fake_skyflow()
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        with self.assertRaises(NotImplementedError):
            client.connection()
        with self.assertRaises(NotImplementedError):
            client.add_connection_config({})
        with self.assertRaises(NotImplementedError):
            client.remove_connection_config("x")
        with self.assertRaises(NotImplementedError):
            client.update_connection_config({})
        with self.assertRaises(NotImplementedError):
            client.get_connection_config("x")

    def test_detect_raises_when_detect_cls_not_supplied(self):
        Skyflow = make_fake_skyflow()
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        with self.assertRaises(NotImplementedError):
            client.detect()

    def test_connection_config_crud_when_supplied(self):
        Skyflow = make_fake_skyflow(with_connections=True)
        connection_config = {"connection_id": "conn1", "connection_url": "https://x", "credentials": {"token": "t"}}
        client = Skyflow.builder().add_connection_config(connection_config).build()

        self.assertIsInstance(client.connection("conn1"), FakeConnection)

        updated = dict(connection_config)
        updated["connection_url"] = "https://y"
        client.update_connection_config(updated)
        self.assertEqual(client.get_connection_config("conn1").get("connection_url"), "https://y")

        client.remove_connection_config("conn1")
        with self.assertRaises(SkyflowError):
            client.get_connection_config("conn1")

    def test_detect_returns_detect_controller_when_supplied(self):
        Skyflow = make_fake_skyflow(with_detect=True)
        client = Skyflow.builder().add_vault_config(VAULT_CONFIG).build()
        self.assertIsInstance(client.detect("v1"), FakeDetect)

    def test_make_skyflow_class_requires_connection_validators_when_connection_cls_given(self):
        with self.assertRaises(ValueError):
            make_skyflow_class(
                vault_client_cls=FakeVaultClient,
                vault_controller_cls=FakeVaultController,
                logger_cls=Logger,
                default_log_level=LogLevel.ERROR,
                skyflow_messages=SkyflowMessages,
                validate_vault_config=_noop_validate,
                validate_update_vault_config=_noop_validate,
                validate_log_level=_noop_validate,
                validate_credentials=_noop_validate,
                connection_cls=FakeConnection,
                # validate_connection_config/validate_update_connection_config omitted on purpose
            )


class TestBaseSkyflowInterface(unittest.TestCase):
    def test_using_the_template_builder_directly_raises_with_a_clear_message(self):
        with self.assertRaises(NotImplementedError) as ctx:
            BaseSkyflow.Builder()
        self.assertIn("make_skyflow_class()", str(ctx.exception))
        self.assertIn("_vault_client_cls", str(ctx.exception))

    def test_make_skyflow_class_produced_builder_constructs_fine(self):
        Skyflow = make_fake_skyflow()
        self.assertIsInstance(Skyflow.builder(), BaseSkyflow.Builder)

    def test_instantiating_base_skyflow_directly_raises(self):
        with self.assertRaises(SkyflowError):
            BaseSkyflow(None)


if __name__ == "__main__":
    unittest.main()
