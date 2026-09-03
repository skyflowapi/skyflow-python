import unittest

from skyflow.utils._response_parsing import parse_tokens, parse_hashed_data, parse_metadata


class TestParseTokens(unittest.TestCase):
    def test_list_of_entries_normalized_to_snake_case(self):
        raw = {"ssn": [
            {"token": "t1", "tokenGroupName": "g1", "path": "p1"},
            {"token": "t2", "tokenGroupName": "g2"},
        ]}
        self.assertEqual(parse_tokens(raw), {"ssn": [
            {"token": "t1", "token_group_name": "g1", "path": "p1"},
            {"token": "t2", "token_group_name": "g2", "path": None},
        ]})

    def test_single_unwrapped_entry_becomes_a_list(self):
        self.assertEqual(
            parse_tokens({"ssn": {"token": "t1", "tokenGroupName": "g1"}}),
            {"ssn": [{"token": "t1", "token_group_name": "g1", "path": None}]},
        )

    def test_bare_value_becomes_a_token(self):
        self.assertEqual(
            parse_tokens({"ssn": "bare"}),
            {"ssn": [{"token": "bare", "token_group_name": None, "path": None}]},
        )

    def test_none_returns_none(self):
        self.assertIsNone(parse_tokens(None))

    def test_none_column_value_is_skipped(self):
        self.assertEqual(parse_tokens({"ssn": None}), {})

    def test_none_entry_in_list_is_dropped(self):
        self.assertEqual(parse_tokens({"ssn": [None]}), {"ssn": []})


class TestParseHashedData(unittest.TestCase):
    def test_list_of_hash_entries(self):
        raw = {"ssn": [{"data": "h", "hashName": "hash1"}]}
        self.assertEqual(parse_hashed_data(raw), {"ssn": [{"data": "h", "hash_name": "hash1"}]})

    def test_bare_value_wrapped(self):
        self.assertEqual(
            parse_hashed_data({"email": "abc"}),
            {"email": [{"data": "abc", "hash_name": None}]},
        )

    def test_none_returns_none(self):
        self.assertIsNone(parse_hashed_data(None))

    def test_none_entry_in_list_is_dropped(self):
        self.assertEqual(parse_hashed_data({"ssn": [None]}), {"ssn": []})


class TestParseMetadata(unittest.TestCase):
    def test_reads_both_casings(self):
        self.assertEqual(parse_metadata({"skyflowID": "id", "tableName": "t1"}),
                         {"skyflow_id": "id", "table_name": "t1"})
        self.assertEqual(parse_metadata({"skyflowId": "id", "table": "t1"}),
                         {"skyflow_id": "id", "table_name": "t1"})

    def test_none_returns_none(self):
        self.assertIsNone(parse_metadata(None))


if __name__ == "__main__":
    unittest.main()
