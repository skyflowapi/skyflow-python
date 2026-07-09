import unittest

from common.vault.data import BaseInsertRequest, BaseInsertResponse


class TestBaseInsertRequest(unittest.TestCase):
    def test_table_and_values_are_required(self):
        with self.assertRaises(TypeError):
            BaseInsertRequest()

    def test_upsert_defaults_to_none(self):
        request = BaseInsertRequest(table="t1", values=[{"values": {"a": 1}}])
        self.assertIsNone(request.upsert)

    def test_construction(self):
        request = BaseInsertRequest(table="t1", values=[{"values": {"a": 1}}], upsert="upsert_val")
        self.assertEqual(request.table, "t1")
        self.assertEqual(request.values, [{"values": {"a": 1}}])
        self.assertEqual(request.upsert, "upsert_val")


class TestBaseInsertResponse(unittest.TestCase):
    def test_defaults(self):
        response = BaseInsertResponse()
        self.assertIsNone(response.inserted_fields)
        self.assertIsNone(response.errors)

    def test_repr_uses_subclass_name(self):
        class InsertResponse(BaseInsertResponse):
            pass

        response = InsertResponse(inserted_fields=[{"skyflow_id": "id1"}], errors=None)
        self.assertIn("InsertResponse", repr(response))
        self.assertNotIn("BaseInsertResponse", repr(response))

    def test_str_matches_repr(self):
        response = BaseInsertResponse(inserted_fields=[], errors=[])
        self.assertEqual(str(response), repr(response))


if __name__ == "__main__":
    unittest.main()
