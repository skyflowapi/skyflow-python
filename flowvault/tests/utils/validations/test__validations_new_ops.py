import unittest

from common.errors import SkyflowError
from skyflow.utils.validations import (
    validate_query_request,
    validate_get_tokens_request,
    validate_upload_files_request,
    validate_delete_files_request,
)
from skyflow.vault.data import (
    QueryRequest,
    GetTokensRequest,
    GetTokensRequestRecord,
    UploadFilesRequest,
    UploadFilesRequestRecord,
    UploadFilesRequestColumn,
    DeleteFilesRequest,
    DeleteFilesRequestRecord,
)


class TestValidateQueryRequest(unittest.TestCase):
    def test_valid(self):
        validate_query_request(None, QueryRequest(query="SELECT 1"))

    def test_blank_raises(self):
        with self.assertRaises(SkyflowError):
            validate_query_request(None, QueryRequest(query="   "))

    def test_empty_raises(self):
        with self.assertRaises(SkyflowError):
            validate_query_request(None, QueryRequest(query=""))

    def test_non_string_raises(self):
        with self.assertRaises(SkyflowError):
            validate_query_request(None, QueryRequest(query=123))


class TestValidateGetTokensRequest(unittest.TestCase):
    def test_valid(self):
        validate_get_tokens_request(None, GetTokensRequest(records=[
            GetTokensRequestRecord(value="v", token_group_name="g"),
        ]))

    def test_empty_records_raises(self):
        with self.assertRaises(SkyflowError):
            validate_get_tokens_request(None, GetTokensRequest(records=[]))

    def test_non_record_item_raises(self):
        with self.assertRaises(SkyflowError):
            validate_get_tokens_request(None, GetTokensRequest(records=["not-a-record"]))

    def test_none_value_raises(self):
        with self.assertRaises(SkyflowError):
            validate_get_tokens_request(None, GetTokensRequest(records=[
                GetTokensRequestRecord(value=None, token_group_name="g"),
            ]))

    def test_blank_token_group_name_raises(self):
        with self.assertRaises(SkyflowError):
            validate_get_tokens_request(None, GetTokensRequest(records=[
                GetTokensRequestRecord(value="v", token_group_name="  "),
            ]))


class TestValidateUploadFilesRequest(unittest.TestCase):
    def _column(self, **kwargs):
        kwargs.setdefault("column", "c")
        kwargs.setdefault("file_path", "/tmp/x")
        return UploadFilesRequestColumn(**kwargs)

    def test_valid(self):
        validate_upload_files_request(None, UploadFilesRequest(records=[
            UploadFilesRequestRecord(table_name="t1", columns=[self._column()]),
        ]))

    def test_empty_records_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[]))

    def test_missing_table_name_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="  ", columns=[self._column()]),
            ]))

    def test_empty_columns_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="t1", columns=[]),
            ]))

    def test_missing_column_name_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="t1", columns=[
                    UploadFilesRequestColumn(column="  ", file_path="/tmp/x"),
                ]),
            ]))

    def test_no_file_source_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="t1", columns=[UploadFilesRequestColumn(column="c")]),
            ]))

    def test_multiple_file_sources_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="t1", columns=[
                    UploadFilesRequestColumn(column="c", file_path="/tmp/x", base64="abc"),
                ]),
            ]))

    def test_base64_without_file_name_raises(self):
        with self.assertRaises(SkyflowError):
            validate_upload_files_request(None, UploadFilesRequest(records=[
                UploadFilesRequestRecord(table_name="t1", columns=[
                    UploadFilesRequestColumn(column="c", base64="abc"),
                ]),
            ]))

    def test_base64_with_file_name_valid(self):
        validate_upload_files_request(None, UploadFilesRequest(records=[
            UploadFilesRequestRecord(table_name="t1", columns=[
                UploadFilesRequestColumn(column="c", base64="abc", file_name="x.bin"),
            ]),
        ]))


class TestValidateDeleteFilesRequest(unittest.TestCase):
    def test_valid_by_skyflow_id(self):
        validate_delete_files_request(None, DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1"),
        ]))

    def test_valid_by_unique_values(self):
        validate_delete_files_request(None, DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], unique_values=[{"email": "a@b.com"}]),
        ]))

    def test_empty_records_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[]))

    def test_missing_table_name_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="  ", columns=["c"], skyflow_id="id1"),
            ]))

    def test_empty_columns_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="t1", columns=[], skyflow_id="id1"),
            ]))

    def test_non_string_columns_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="t1", columns=[1, 2], skyflow_id="id1"),
            ]))

    def test_neither_selector_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="t1", columns=["c"]),
            ]))

    def test_both_selectors_raises(self):
        with self.assertRaises(SkyflowError):
            validate_delete_files_request(None, DeleteFilesRequest(records=[
                DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1", unique_values=[{"email": "a@b.com"}]),
            ]))


if __name__ == "__main__":
    unittest.main()
