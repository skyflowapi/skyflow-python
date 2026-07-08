import unittest

from common.errors import SkyflowError
from common.utils.enums import Env
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.utils.validations import validate_insert_request, validate_vault_config
from skyflow_flowvault.vault.data import InsertRequest, Upsert


class TestValidateInsertRequest(unittest.TestCase):
    def test_valid_minimal_request(self):
        request = InsertRequest(records=[dict(values={"a": 1})], table="t1")
        validate_insert_request(None, request)  # should not raise

    def test_valid_rich_request_with_per_record_overrides(self):
        """Valid per-record use: no request-level table/upsert at all (the vault rejects
        setting it in both places -- see test_table_in_both_places_raises below). Java parity
        requires EVERY record to set its own table when there's no request-level table (a
        partial mix is invalid -- see test_table_missing_from_one_record_raises), so both
        records set their own here."""
        request = InsertRequest(
            records=[
                dict(values={"a": 1}, table="t2"),
                dict(values={"a": 2}, table="t2", upsert=Upsert(update_type=UpsertType.REPLACE, unique_columns=["a"])),
            ],
        )
        validate_insert_request(None, request)  # should not raise

    def test_table_in_both_places_raises(self):
        """Confirmed directly against a real vault: 'Table name should be present outside the
        records or inside each record. Should be present at one place.'"""
        request = InsertRequest(
            records=[dict(values={"a": 1}, table="t2")],
            table="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_table_in_both_places_raises_even_if_only_one_record_sets_it(self):
        request = InsertRequest(
            records=[dict(values={"a": 1}, table="t2"), dict(values={"a": 2})],
            table="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_record_level_upsert_forbidden_when_table_is_at_request_level(self):
        """Java parity: 'upsert' must live at the SAME place as 'table'. Here table is at the
        request level, so a record-level upsert is rejected even though this record's own table
        placement (none) is fine."""
        request = InsertRequest(
            records=[dict(values={"a": 1}, upsert=Upsert(unique_columns=["b"]))],
            table="t1",
            upsert=Upsert(unique_columns=["a"]),
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_request_level_upsert_forbidden_when_table_is_per_record(self):
        request = InsertRequest(
            records=[dict(values={"a": 1}, table="t1")],
            upsert=Upsert(unique_columns=["a"]),
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_too_many_records_raises(self):
        request = InsertRequest(records=[dict(values={"a": 1}) for _ in range(10001)], table="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_exactly_max_records_is_valid(self):
        request = InsertRequest(records=[dict(values={"a": 1}) for _ in range(10000)], table="t1")
        validate_insert_request(None, request)  # should not raise

    def test_table_missing_from_one_record_raises(self):
        """Java parity: when there's no request-level table, EVERY record must set its own --
        a partial mix (some records with a table, some without) is invalid."""
        request = InsertRequest(records=[dict(values={"a": 1}, table="t1"), dict(values={"a": 2})])
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    # Empty/null key or value in a record's 'values', and record 'values' being a non-empty
    # dict, are now validated by the controller via the shared
    # BaseVaultController._validate_field_values() -- see test__vault.py's
    # test_insert_raises_on_empty_key/_on_empty_value/_on_non_dict_values/_on_empty_values, and
    # common/tests/vault/test_base_vault.py for the shared helper's own unit tests.

    def test_falsy_non_string_values_are_valid(self):
        """0, False, [], {} are all legitimate values -- only None/empty-string should raise
        (mirrors Java's value.toString().trim().isEmpty(), which is non-empty for all of these)."""
        request = InsertRequest(records=[dict(values={"a": 0, "b": False, "c": [], "d": {}})], table="t1")
        validate_insert_request(None, request)  # should not raise

    def test_request_level_table_alone_is_valid(self):
        request = InsertRequest(records=[dict(values={"a": 1}), dict(values={"a": 2})], table="t1")
        validate_insert_request(None, request)  # should not raise

    def test_per_record_table_alone_is_valid(self):
        request = InsertRequest(records=[dict(values={"a": 1}, table="t1"), dict(values={"a": 2}, table="t2")])
        validate_insert_request(None, request)  # should not raise

    def test_records_must_be_a_list(self):
        request = InsertRequest(records="not-a-list", table="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_records_must_be_dicts(self):
        request = InsertRequest(records=["not-a-dict"], table="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_record_with_unknown_key_raises(self):
        request = InsertRequest(records=[{"a": 1}], table="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_records_must_not_be_empty(self):
        request = InsertRequest(records=[], table="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    # Table name format (non-empty string if provided) is now validated by the controller via
    # the shared BaseVaultController._validate_table_name_if_present() -- see
    # test__vault.py's test_insert_raises_on_invalid_table_name and
    # common/tests/vault/test_base_vault.py for the shared helper's own unit tests.

    def test_table_is_optional_when_every_record_has_its_own(self):
        request = InsertRequest(records=[dict(values={"a": 1}, table="t2")])
        validate_insert_request(None, request)  # should not raise

    def test_upsert_must_be_an_upsert_instance(self):
        request = InsertRequest(records=[dict(values={"a": 1})], table="t1", upsert="not-an-upsert")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_upsert_unique_columns_must_be_non_empty_list_of_strings(self):
        request = InsertRequest(records=[dict(values={"a": 1})], table="t1", upsert=Upsert(unique_columns=[]))
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_upsert_update_type_must_be_upsert_type_enum(self):
        request = InsertRequest(
            records=[dict(values={"a": 1})], table="t1",
            upsert=Upsert(update_type="REPLACE", unique_columns=["a"]),  # plain string, not the enum
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_per_record_upsert_is_also_validated(self):
        request = InsertRequest(
            records=[dict(values={"a": 1}, upsert=Upsert(unique_columns=[]))],
            table="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)


class TestValidateVaultConfig(unittest.TestCase):
    def test_valid_config(self):
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster1",
            "env": Env.PROD,
            # api_key (not a JWT-format "token") avoids the expiry check so this only
            # exercises validate_vault_config's own structural validation.
            "credentials": {"api_key": "sky-abcde-" + "f" * 32},
        }
        self.assertTrue(validate_vault_config(None, config))

    def test_missing_vault_id_raises(self):
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, {"cluster_id": "cluster1"})

    def test_unknown_key_raises(self):
        config = {"vault_id": "v", "cluster_id": "c", "unexpected_key": True}
        with self.assertRaises(SkyflowError):
            validate_vault_config(None, config)


if __name__ == "__main__":
    unittest.main()
