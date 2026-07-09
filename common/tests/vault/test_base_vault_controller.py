import unittest

from common.errors import SkyflowError
from common.utils import SkyflowMessages
from common.vault.base_vault_controller import BaseVaultController


class DummyVaultController(BaseVaultController):
    _skyflow_messages = SkyflowMessages

    def insert(self, request):
        raise NotImplementedError

    def get(self, request):
        raise NotImplementedError

    def update(self, request):
        raise NotImplementedError

    def delete(self, request):
        raise NotImplementedError

    def query(self, request):
        raise NotImplementedError

    def detokenize(self, request):
        raise NotImplementedError


class TestBaseVaultControllerAbstractContract(unittest.TestCase):
    def test_cannot_instantiate_without_insert(self):
        class Incomplete(BaseVaultController):
            pass

        with self.assertRaises(TypeError):
            Incomplete(vault_client=None)

    def test_cannot_instantiate_missing_any_single_method(self):
        """Java-interface-style: every one of the six operations is independently required --
        omitting any single one (not just insert) blocks instantiation."""
        for missing in ("insert", "get", "update", "delete", "query", "detokenize"):
            methods = {name: (lambda self, request: None) for name in
                       ("insert", "get", "update", "delete", "query", "detokenize") if name != missing}
            Incomplete = type("Incomplete", (BaseVaultController,), methods)
            with self.assertRaises(TypeError, msg=f"missing only '{missing}' should still fail to instantiate"):
                Incomplete(vault_client=None)

    def test_concrete_subclass_instantiates(self):
        vault = DummyVaultController(vault_client=None)
        self.assertIsInstance(vault, BaseVaultController)


class TestValidateTableNameIfPresent(unittest.TestCase):
    """Shared rule used identically by both variants (see PdbVaultController/flowvault's
    VaultController.insert()): a table value, IF given, must be a non-empty string. Whether
    table is required at all is variant-specific and stays out of this helper."""

    def setUp(self):
        self.vault = DummyVaultController(vault_client=None)

    def test_none_is_allowed(self):
        self.vault._validate_table_name_if_present(None)  # should not raise

    def test_valid_string_is_allowed(self):
        self.vault._validate_table_name_if_present("table1")  # should not raise

    def test_empty_string_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_table_name_if_present("")

    def test_whitespace_only_string_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_table_name_if_present("   ")

    def test_non_string_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_table_name_if_present(123)


class TestValidateFieldValues(unittest.TestCase):
    """Shared rule: a record's field-value map must be a non-empty dict of non-empty string
    keys and non-null/non-empty-string values -- the exact check your lead called out as
    belonging in a protected base-controller helper."""

    def setUp(self):
        self.vault = DummyVaultController(vault_client=None)

    def test_valid_values_pass(self):
        self.vault._validate_field_values({"name": "John", "age": 30})  # should not raise

    def test_none_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values(None)

    def test_non_dict_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values(["not", "a", "dict"])

    def test_empty_dict_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values({})

    def test_empty_key_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values({"": "value"})

    def test_whitespace_only_key_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values({"   ": "value"})

    def test_none_value_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values({"a": None})

    def test_empty_string_value_raises(self):
        with self.assertRaises(SkyflowError):
            self.vault._validate_field_values({"a": ""})

    def test_falsy_non_string_values_are_valid(self):
        """0, False, [], {} are all legitimate values -- only None/empty-string should raise."""
        self.vault._validate_field_values({"a": 0, "b": False, "c": [], "d": {}})  # should not raise


if __name__ == "__main__":
    unittest.main()
