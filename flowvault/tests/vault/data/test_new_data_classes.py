import unittest

from common.vault.data import (
    BaseQueryRequest,
    BaseQueryResponse,
    BaseGetTokensRequest,
    BaseGetTokensResponse,
    BaseUploadFilesRequest,
    BaseUploadFilesResponse,
    BaseDeleteFilesRequest,
    BaseDeleteFilesResponse,
)
from skyflow.utils.enums import FileUploadStatus
from skyflow.vault.data import (
    QueryRequest,
    QueryOptions,
    QueryResponse,
    QueryResponseRecord,
    QueryResponseMetadata,
    GetTokensRequest,
    GetTokensRequestRecord,
    GetTokensOptions,
    GetTokensResponse,
    GetTokensResponseRecord,
    UploadFilesRequest,
    UploadFilesRequestRecord,
    UploadFilesRequestColumn,
    UploadFilesOptions,
    UploadFilesResponse,
    UploadFilesResponseRecord,
    UploadFilesColumnResult,
    DeleteFilesRequest,
    DeleteFilesRequestRecord,
    DeleteFilesOptions,
    DeleteFilesResponse,
    DeleteFilesResponseRecord,
    DeleteFilesColumnResult,
)


class TestQueryDataClasses(unittest.TestCase):
    def test_request_extends_base(self):
        request = QueryRequest(query="SELECT 1")
        self.assertIsInstance(request, BaseQueryRequest)
        self.assertEqual(request.query, "SELECT 1")

    def test_options_default_none(self):
        self.assertIsNone(QueryOptions().interceptor)

    def test_record_and_metadata(self):
        record = QueryResponseRecord(data={"a": 1})
        metadata = QueryResponseMetadata(columns=["a"])
        self.assertEqual(record.data, {"a": 1})
        self.assertEqual(metadata.columns, ["a"])
        self.assertIn("QueryResponseRecord", repr(record))
        self.assertIn("QueryResponseMetadata", str(metadata))

    def test_response_extends_base_and_repr(self):
        response = QueryResponse(records=[QueryResponseRecord(data={"a": 1})],
                                 metadata=QueryResponseMetadata(columns=["a"]), request_id="rid")
        self.assertIsInstance(response, BaseQueryResponse)
        self.assertEqual(response.request_id, "rid")
        self.assertIn("QueryResponse", repr(response))
        self.assertIn("request_id", str(response))


class TestGetTokensDataClasses(unittest.TestCase):
    def test_request_extends_base(self):
        request = GetTokensRequest(records=[GetTokensRequestRecord(value="v", token_group_name="g")])
        self.assertIsInstance(request, BaseGetTokensRequest)
        self.assertEqual(request.records[0].value, "v")
        self.assertEqual(request.records[0].token_group_name, "g")

    def test_options_default_none(self):
        self.assertIsNone(GetTokensOptions().interceptor)

    def test_response_and_record(self):
        record = GetTokensResponseRecord(value="v", token_group_name="g", token="tok", http_code=200, error=None, request_id=None)
        response = GetTokensResponse(records=[record])
        self.assertIsInstance(response, BaseGetTokensResponse)
        self.assertEqual(response.records[0].token, "tok")
        self.assertIn("GetTokensResponseRecord", repr(record))
        self.assertIn("GetTokensResponse", repr(response))


class TestUploadFilesDataClasses(unittest.TestCase):
    def test_request_extends_base(self):
        column = UploadFilesRequestColumn(column="c", file_path="/tmp/x")
        request = UploadFilesRequest(records=[UploadFilesRequestRecord(table_name="t1", columns=[column])])
        self.assertIsInstance(request, BaseUploadFilesRequest)
        self.assertEqual(request.records[0].table_name, "t1")
        self.assertIsNone(request.records[0].skyflow_id)
        self.assertEqual(request.records[0].columns[0].column, "c")

    def test_column_accepts_each_source(self):
        self.assertEqual(UploadFilesRequestColumn(column="c", file_path="/p").file_path, "/p")
        self.assertEqual(UploadFilesRequestColumn(column="c", base64="b", file_name="n").base64, "b")
        sentinel = object()
        self.assertIs(UploadFilesRequestColumn(column="c", file_object=sentinel).file_object, sentinel)

    def test_options_default_none(self):
        self.assertIsNone(UploadFilesOptions().interceptor)

    def test_response_record_and_column_result(self):
        column_result = UploadFilesColumnResult(column="c", file_name="f.txt",
                                                upload_status=FileUploadStatus.UPLOADED.value, error=None)
        record = UploadFilesResponseRecord(skyflow_id="sid", table_name="t1", columns=[column_result], http_code=200)
        response = UploadFilesResponse(records=[record])
        self.assertIsInstance(response, BaseUploadFilesResponse)
        self.assertEqual(response.records[0].columns[0].upload_status, "UPLOADED")
        self.assertFalse(hasattr(column_result, "signed_url"))
        self.assertIn("UploadFilesColumnResult", repr(column_result))
        self.assertIn("UploadFilesResponseRecord", repr(record))
        self.assertIn("UploadFilesResponse", repr(response))


class TestDeleteFilesDataClasses(unittest.TestCase):
    def test_request_extends_base(self):
        request = DeleteFilesRequest(records=[
            DeleteFilesRequestRecord(table_name="t1", columns=["c"], skyflow_id="id1"),
        ])
        self.assertIsInstance(request, BaseDeleteFilesRequest)
        self.assertEqual(request.records[0].columns, ["c"])
        self.assertEqual(request.records[0].skyflow_id, "id1")
        self.assertIsNone(request.records[0].unique_values)

    def test_options_default_none(self):
        self.assertIsNone(DeleteFilesOptions().interceptor)

    def test_response_record_and_column_result(self):
        column_result = DeleteFilesColumnResult(column="c", status="DELETED")
        record = DeleteFilesResponseRecord(skyflow_id="id1", table_name="t1", columns=[column_result], http_code=200)
        response = DeleteFilesResponse(records=[record])
        self.assertIsInstance(response, BaseDeleteFilesResponse)
        self.assertEqual(response.records[0].columns[0].status, "DELETED")
        self.assertIn("DeleteFilesColumnResult", repr(column_result))
        self.assertIn("DeleteFilesResponseRecord", repr(record))
        self.assertIn("DeleteFilesResponse", str(response))


class TestFileUploadStatusEnum(unittest.TestCase):
    def test_values(self):
        self.assertEqual(FileUploadStatus.UPLOADED.value, "UPLOADED")
        self.assertEqual(FileUploadStatus.FAILED.value, "FAILED")
        self.assertEqual(FileUploadStatus.SKIPPED.value, "SKIPPED")


if __name__ == "__main__":
    unittest.main()
