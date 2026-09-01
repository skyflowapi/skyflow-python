import unittest

from common.errors import SkyflowError
from common.utils.enums import Env
from skyflow_flowvault.utils.enums import UpsertType
from skyflow_flowvault.utils.validations import (
    validate_insert_request,
    validate_get_request,
    validate_update_request,
    validate_delete_request,
    validate_detokenize_request,
    validate_query_request,
    validate_vault_config,
)
from skyflow_flowvault.vault.data import (
    UpsertOptions,
    ColumnRedaction,
    InsertRequestRecord,
    InsertRequest,
    GetRequest,
    GetRecordRequest,
    UpdateRequest,
    DeleteRequest,
    DetokenizeRequest,
    QueryRequest,
)


class TestValidateInsertRequest(unittest.TestCase):
    def test_valid_minimal_request(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1")
        validate_insert_request(None, request)  # should not raise

    def test_valid_rich_request_with_per_record_overrides(self):
        """Valid per-record use: no request-level table/upsert at all (the vault rejects
        setting it in both places -- see test_table_in_both_places_raises below). Java parity
        requires EVERY record to set its own table when there's no request-level table (a
        partial mix is invalid -- see test_table_missing_from_one_record_raises), so both
        records set their own here."""
        request = InsertRequest(
            records=[
                InsertRequestRecord(data={"a": 1}, table_name="t2"),
                InsertRequestRecord(data={"a": 2}, table_name="t2", upsert=UpsertOptions(update_type= UpsertType.REPLACE, unique_columns= ["a"])),
            ],
        )
        validate_insert_request(None, request)  # should not raise

    def test_table_in_both_places_raises(self):
        """Confirmed directly against a real vault: 'Table name should be present outside the
        records or inside each record. Should be present at one place.'"""
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, table_name="t2")],
            table_name="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_table_in_both_places_raises_even_if_only_one_record_sets_it(self):
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, table_name="t2"), InsertRequestRecord(data={"a": 2})],
            table_name="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_record_level_upsert_forbidden_when_table_is_at_request_level(self):
        """Java parity: 'upsert' must live at the SAME place as 'table'. Here table is at the
        request level, so a record-level upsert is rejected even though this record's own table
        placement (none) is fine."""
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, upsert=UpsertOptions(unique_columns= ["b"]))],
            table_name="t1",
            upsert=UpsertOptions(unique_columns= ["a"]),
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_request_level_upsert_forbidden_when_table_is_per_record(self):
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, table_name="t1")],
            upsert=UpsertOptions(unique_columns= ["a"]),
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_too_many_records_raises(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}) for _ in range(10001)], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_exactly_max_records_is_valid(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}) for _ in range(10000)], table_name="t1")
        validate_insert_request(None, request)  # should not raise

    def test_table_missing_from_one_record_raises(self):
        """Java parity: when there's no request-level table, EVERY record must set its own --
        a partial mix (some records with a table, some without) is invalid."""
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}, table_name="t1"), InsertRequestRecord(data={"a": 2})])
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    # Empty/null key or value in a record's 'values', and record 'values' being a non-empty
    # dict, are now validated by the controller via the shared
    # BaseVaultController._validate_field_values() -- see test__vault.py's
    # test_insert_raises_on_empty_key/_on_empty_value/_on_non_dict_values/_on_empty_values, and
    # common/tests/vault/test_base_vault_controller.py for the shared helper's own unit tests.

    def test_falsy_non_string_values_are_valid(self):
        """0, False, [], {} are all legitimate values -- only None/empty-string should raise
        (mirrors Java's value.toString().trim().isEmpty(), which is non-empty for all of these)."""
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 0, "b": False, "c": [], "d": {}})], table_name="t1")
        validate_insert_request(None, request)  # should not raise

    def test_request_level_table_alone_is_valid(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}), InsertRequestRecord(data={"a": 2})], table_name="t1")
        validate_insert_request(None, request)  # should not raise

    def test_per_record_table_alone_is_valid(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}, table_name="t1"), InsertRequestRecord(data={"a": 2}, table_name="t2")])
        validate_insert_request(None, request)  # should not raise

    def test_records_must_be_a_list(self):
        request = InsertRequest(records="not-a-list", table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_records_must_be_dicts(self):
        request = InsertRequest(records=["not-a-dict"], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_record_with_unknown_key_raises(self):
        request = InsertRequest(records=[{"a": 1}], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_records_must_not_be_empty(self):
        request = InsertRequest(records=[], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    # Table name format (non-empty string if provided) is now validated by the controller via
    # the shared BaseVaultController._validate_table_name_if_present() -- see
    # test__vault.py's test_insert_raises_on_invalid_table_name and
    # common/tests/vault/test_base_vault_controller.py for the shared helper's own unit tests.

    def test_table_is_optional_when_every_record_has_its_own(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1}, table_name="t2")])
        validate_insert_request(None, request)  # should not raise

    def test_upsert_must_be_a_dict(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1", upsert="not-an-upsert")
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_upsert_unique_columns_must_be_non_empty_list_of_strings(self):
        request = InsertRequest(records=[InsertRequestRecord(data={"a": 1})], table_name="t1", upsert=UpsertOptions(unique_columns= []))
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_upsert_update_type_must_be_upsert_type_enum(self):
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1})], table_name="t1",
            upsert=UpsertOptions(update_type= "REPLACE", unique_columns= ["a"]),  # plain string, not the enum
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)

    def test_per_record_upsert_is_also_validated(self):
        request = InsertRequest(
            records=[InsertRequestRecord(data={"a": 1}, upsert=UpsertOptions(unique_columns= []))],
            table_name="t1",
        )
        with self.assertRaises(SkyflowError):
            validate_insert_request(None, request)


class TestValidateGetRequest(unittest.TestCase):
    def test_valid_request_with_ids(self):
        request = GetRequest(table="t1", ids=["id1"])
        validate_get_request(None, request)  # should not raise

    def test_valid_request_with_unique_values(self):
        request = GetRequest(table="t1", unique_values=[{"email": "a@b.com"}])
        validate_get_request(None, request)  # should not raise

    def test_missing_table_raises(self):
        request = GetRequest(table=None, ids=["id1"])
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)

    def test_empty_table_raises(self):
        request = GetRequest(table="", ids=["id1"])
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)

    def test_missing_ids_and_unique_values_raises(self):
        request = GetRequest(table="t1")
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)

    def test_ids_must_be_a_list(self):
        request = GetRequest(table="t1", ids="not-a-list")
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)

    def test_ids_must_be_non_empty(self):
        request = GetRequest(table="t1", ids=[])
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)

    def test_ids_must_be_strings(self):
        request = GetRequest(table="t1", ids=[123])
        with self.assertRaises(SkyflowError):
            validate_get_request(None, request)


class TestValidateUpdateRequest(unittest.TestCase):
    def test_valid_request_with_request_level_table(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1")
        validate_update_request(None, request)  # should not raise

    def test_valid_request_with_per_record_table(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}, "table_name": "t1"}])
        validate_update_request(None, request)  # should not raise

    def test_records_must_be_a_list(self):
        request = UpdateRequest(records="not-a-list", table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_records_must_not_be_empty(self):
        request = UpdateRequest(records=[], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_missing_skyflow_id_raises(self):
        request = UpdateRequest(records=[{"data": {"a": 1}}], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_empty_skyflow_id_raises(self):
        request = UpdateRequest(records=[{"skyflow_id": "  ", "data": {"a": 1}}], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_record_with_unknown_key_raises(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "unexpected": 1}], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_table_in_both_places_raises(self):
        request = UpdateRequest(records=[{"skyflow_id": "id1", "data": {"a": 1}, "table_name": "t2"}], table_name="t1")
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_table_missing_from_one_record_raises(self):
        request = UpdateRequest(records=[
            {"skyflow_id": "id1", "data": {"a": 1}, "table_name": "t1"},
            {"skyflow_id": "id2", "data": {"a": 2}},
        ])
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_invalid_update_type_raises(self):
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1", update_type="REPLACE",
        )
        with self.assertRaises(SkyflowError):
            validate_update_request(None, request)

    def test_valid_update_type_enum_is_valid(self):
        request = UpdateRequest(
            records=[{"skyflow_id": "id1", "data": {"a": 1}}], table_name="t1", update_type=UpsertType.REPLACE,
        )
        validate_update_request(None, request)  # should not raise


class TestValidateDeleteRequest(unittest.TestCase):
    def test_valid_request_with_ids(self):
        request = DeleteRequest(table="t1", ids=["id1"])
        validate_delete_request(None, request)  # should not raise

    def test_valid_request_with_unique_values(self):
        request = DeleteRequest(table="t1", unique_values=[{"email": "a@b.com"}])
        validate_delete_request(None, request)  # should not raise

    def test_missing_table_raises(self):
        request = DeleteRequest(table=None, ids=["id1"])
        with self.assertRaises(SkyflowError):
            validate_delete_request(None, request)

    def test_missing_ids_and_unique_values_raises(self):
        request = DeleteRequest(table="t1")
        with self.assertRaises(SkyflowError):
            validate_delete_request(None, request)

    def test_ids_must_be_non_empty(self):
        request = DeleteRequest(table="t1", ids=[])
        with self.assertRaises(SkyflowError):
            validate_delete_request(None, request)

    def test_ids_must_be_strings(self):
        request = DeleteRequest(table="t1", ids=[123])
        with self.assertRaises(SkyflowError):
            validate_delete_request(None, request)


class TestValidateDetokenizeRequest(unittest.TestCase):
    def test_valid_request(self):
        request = DetokenizeRequest(tokens=["tok1", "tok2"])
        validate_detokenize_request(None, request)  # should not raise

    def test_valid_request_with_token_group_redactions(self):
        request = DetokenizeRequest(
            tokens=["tok1"], token_group_redactions=[{"token_group_name": "g1", "redaction": "mask1"}],
        )
        validate_detokenize_request(None, request)  # should not raise

    def test_tokens_must_be_a_list(self):
        request = DetokenizeRequest(tokens="not-a-list")
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)

    def test_tokens_must_not_be_empty(self):
        request = DetokenizeRequest(tokens=[])
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)

    def test_tokens_must_be_strings(self):
        request = DetokenizeRequest(tokens=[123])
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)

    def test_empty_string_token_raises(self):
        request = DetokenizeRequest(tokens=["  "])
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)

    def test_invalid_token_group_redactions_raises(self):
        request = DetokenizeRequest(tokens=["tok1"], token_group_redactions=["not-a-dict"])
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)

    def test_token_group_redactions_missing_name_raises(self):
        request = DetokenizeRequest(tokens=["tok1"], token_group_redactions=[{"redaction": "mask1"}])
        with self.assertRaises(SkyflowError):
            validate_detokenize_request(None, request)


class TestValidateQueryRequest(unittest.TestCase):
    def test_valid_request(self):
        validate_query_request(None, QueryRequest(query="SELECT * FROM t1"))  # should not raise

    def test_query_must_be_a_string(self):
        with self.assertRaises(SkyflowError):
            validate_query_request(None, QueryRequest(query=123))

    def test_query_must_not_be_empty(self):
        with self.assertRaises(SkyflowError):
            validate_query_request(None, QueryRequest(query="   "))


class TestValidateGetRequestMultiTable(unittest.TestCase):
    def test_valid_multi_table_request(self):
        request = GetRequest(records=[GetRecordRequest(table="persons", ids=["id1"])])
        validate_get_request(None, request)  # should not raise

    def test_records_must_be_get_record_request_objects(self):
        with self.assertRaises(SkyflowError):
            validate_get_request(None, GetRequest(records=[{"table": "persons", "ids": ["id1"]}]))

    def test_records_must_not_be_empty(self):
        with self.assertRaises(SkyflowError):
            validate_get_request(None, GetRequest(records=[]))

    def test_records_and_single_table_fields_are_mutually_exclusive(self):
        with self.assertRaises(SkyflowError):
            validate_get_request(None, GetRequest(table="persons", records=[GetRecordRequest(table="persons", ids=["id1"])]))

    def test_each_record_needs_a_table(self):
        with self.assertRaises(SkyflowError):
            validate_get_request(None, GetRequest(records=[GetRecordRequest(table=None, ids=["id1"])]))

    def test_each_record_needs_ids_or_unique_values(self):
        with self.assertRaises(SkyflowError):
            validate_get_request(None, GetRequest(records=[GetRecordRequest(table="persons")]))


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
