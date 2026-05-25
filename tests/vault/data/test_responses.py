import unittest
from skyflow.vault.data._delete_response import DeleteResponse
from skyflow.vault.data._file_upload_response import FileUploadResponse
from skyflow.vault.data._get_response import GetResponse
from skyflow.vault.data._insert_response import InsertResponse
from skyflow.vault.data._query_response import QueryResponse
from skyflow.vault.data._update_response import UpdateResponse
from skyflow.vault.data._upload_file_request import UploadFileRequest


class TestDeleteResponse(unittest.TestCase):
    def test_repr(self):
        r = DeleteResponse(deleted_ids=["id1"], errors=None)
        self.assertIn("DeleteResponse", repr(r))
        self.assertIn("id1", repr(r))

    def test_str(self):
        r = DeleteResponse(deleted_ids=["id1"], errors=None)
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = DeleteResponse()
        self.assertIsNone(r.deleted_ids)
        self.assertIsNone(r.errors)


class TestFileUploadResponse(unittest.TestCase):
    def test_repr(self):
        r = FileUploadResponse(skyflow_id="sky123", errors=None)
        self.assertIn("FileUploadResponse", repr(r))
        self.assertIn("sky123", repr(r))

    def test_str(self):
        r = FileUploadResponse(skyflow_id="sky123", errors=None)
        self.assertEqual(str(r), repr(r))


class TestGetResponse(unittest.TestCase):
    def test_repr(self):
        r = GetResponse(data=[{"field": "val"}], errors=None)
        self.assertIn("GetResponse", repr(r))

    def test_str(self):
        r = GetResponse(data=[{"field": "val"}], errors=None)
        self.assertEqual(str(r), repr(r))

    def test_none_data_defaults_to_empty_list(self):
        r = GetResponse(data=None)
        self.assertEqual(r.data, [])

    def test_empty_data_not_replaced(self):
        r = GetResponse(data={})
        self.assertEqual(r.data, {})


class TestInsertResponse(unittest.TestCase):
    def test_repr(self):
        r = InsertResponse(inserted_fields=[{"skyflow_id": "id1"}], errors=None)
        self.assertIn("InsertResponse", repr(r))

    def test_str(self):
        r = InsertResponse(inserted_fields=[{"skyflow_id": "id1"}])
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = InsertResponse()
        self.assertIsNone(r.inserted_fields)
        self.assertIsNone(r.errors)


class TestQueryResponse(unittest.TestCase):
    def test_repr(self):
        r = QueryResponse()
        self.assertIn("QueryResponse", repr(r))

    def test_str(self):
        r = QueryResponse()
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = QueryResponse()
        self.assertEqual(r.fields, [])
        self.assertIsNone(r.errors)


class TestUpdateResponse(unittest.TestCase):
    def test_repr(self):
        r = UpdateResponse(updated_field={"skyflow_id": "id1"}, errors=None)
        self.assertIn("UpdateResponse", repr(r))

    def test_str(self):
        r = UpdateResponse(updated_field={"skyflow_id": "id1"})
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = UpdateResponse()
        self.assertIsNone(r.updated_field)
        self.assertIsNone(r.errors)


class TestUploadFileRequest(unittest.TestCase):
    def test_instantiation(self):
        r = UploadFileRequest()
        self.assertIsNotNone(r)


if __name__ == "__main__":
    unittest.main()
