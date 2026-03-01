import unittest
from unittest.mock import Mock, patch, mock_open as mock_open_func, mock_open
from skyflow.generated.rest import V1BatchRecord, V1FieldRecords, V1DetokenizeRecordRequest, V1TokenizeRecordRequest
from skyflow.utils._skyflow_messages import SkyflowMessages
from skyflow.utils.enums import RedactionType, TokenMode
from skyflow.vault.controller import Vault
from skyflow.vault.data import InsertRequest, InsertResponse, UpdateResponse, UpdateRequest, DeleteResponse, \
    DeleteRequest, GetRequest, GetResponse, QueryRequest, QueryResponse, FileUploadRequest
from skyflow.vault.tokens import DetokenizeRequest, DetokenizeResponse, TokenizeResponse, TokenizeRequest
from skyflow.error import SkyflowError
from skyflow.utils.validations import validate_file_upload_request
VAULT_ID = "test_vault_id"
TABLE_NAME = "test_table"

class TestVault(unittest.TestCase):

    def setUp(self):
        # Mock vault client
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = VAULT_ID
        self.vault_client.get_logger.return_value = Mock()

        # Create a Vault instance with the mock client
        self.vault = Vault(self.vault_client)

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    @patch("skyflow.vault.controller._vault.parse_insert_response")
    def test_insert_with_continue_on_error(self, mock_parse_response, mock_validate):
        """Test insert functionality when continue_on_error is True."""

        # Mock request
        request = InsertRequest(
            table=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=None,
            return_tokens=True,
            upsert='column_name',
            continue_on_error=True
        )

        expected_body = [
            V1BatchRecord(
                fields={"field": "value"},
                table_name=TABLE_NAME,
                method="POST",
                tokenization=True,
                upsert="column_name"
            )
        ]

        # Mock API response to contain a mix of successful and failed insertions
        mock_api_response = Mock()
        mock_api_response.data = {
            "responses":[
                {"Status": 200, "Body": {"records": [{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]}},
                {"Status": 400, "Body": {"error": "Insert error for record 2"}}
            ]
        }

        # Expected parsed response
        expected_inserted_fields = [
            {'skyflow_id': 'id1', 'request_index': 0, 'token_field': 'token_val1'}
        ]
        expected_errors = [
            {'request_index': 1, 'error': 'Insert error for record 2'}
        ]
        expected_response = InsertResponse(inserted_fields=expected_inserted_fields, errors=expected_errors)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.record_service_batch_operation.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response, True)

        # Assert that the result matches the expected InsertResponse
        self.assertEqual(result.inserted_fields, expected_inserted_fields)
        self.assertEqual(result.errors, expected_errors)

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    @patch("skyflow.vault.controller._vault.parse_insert_response")
    def test_insert_with_continue_on_error_false(self, mock_parse_response, mock_validate):
        """Test insert functionality when continue_on_error is False, ensuring a single bulk insert."""

        # Mock request with continue_on_error set to False
        request = InsertRequest(
            table=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=None,
            return_tokens=True,
            upsert=None,
            homogeneous=True,
            continue_on_error=False
        )

        # Expected API request body based on InsertRequest parameters
        expected_body = [
            V1FieldRecords(fields={"field": "value"})
        ]

        # Mock API response for a successful insert
        mock_api_response = Mock()
        mock_api_response.data = {"records":[{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]}
        
        # Expected parsed response
        expected_inserted_fields = [{'skyflow_id': 'id1', 'token_field': 'token_val1'}]
        expected_response = InsertResponse(inserted_fields=expected_inserted_fields)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.record_service_insert_record.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response, False)

        # Assert that the result matches the expected InsertResponse
        self.assertEqual(result.inserted_fields, expected_inserted_fields)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    def test_insert_handles_generic_error(self, mock_validate):
        request = InsertRequest(table="test_table", values=[{"column_name": "value"}], return_tokens=False,
                                upsert=False,
                                homogeneous=False, continue_on_error=False, token_mode=Mock())
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_insert_record.side_effect = Exception("Generic Exception")

        with self.assertRaises(Exception):
            self.vault.insert(request)

        records_api.with_raw_response.record_service_insert_record.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    @patch("skyflow.vault.controller._vault.parse_insert_response")
    def test_insert_with_continue_on_error_false_when_tokens_are_not_none(self, mock_parse_response, mock_validate):
        """Test insert functionality when continue_on_error is False, ensuring a single bulk insert."""

        # Mock request with continue_on_error set to False
        request = InsertRequest(
            table=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=[{"token_field": "token_val1"}],
            return_tokens=True,
            upsert=None,
            homogeneous=True,
            continue_on_error=False
        )

        # Expected API request body based on InsertRequest parameters
        expected_body = [
            V1FieldRecords(fields={"field": "value"}, tokens={"token_field": "token_val1"})
        ]

        # Mock API response for a successful insert
        mock_api_response = Mock()
        mock_api_response.data = {"records":[{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]}
        
        # Expected parsed response
        expected_inserted_fields = [{'skyflow_id': 'id1', 'token_field': 'token_val1'}]
        expected_response = InsertResponse(inserted_fields=expected_inserted_fields)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.record_service_insert_record.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response, False)

        # Assert that the result matches the expected InsertResponse
        self.assertEqual(result.inserted_fields, expected_inserted_fields)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_update_request")
    @patch("skyflow.vault.controller._vault.parse_update_record_response")
    def test_update_successful(self, mock_parse_response, mock_validate):
        """Test update functionality for a successful update request."""

        # Mock request
        request = UpdateRequest(
            table=TABLE_NAME,
            data={"skyflow_id": "12345", "field": "new_value"},
            tokens=None,
            return_tokens=True,
            token_mode=TokenMode.DISABLE
        )

        # Expected payload
        expected_record = V1FieldRecords(fields={"field": "new_value"}, tokens=None)

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.skyflow_id = "12345"
        mock_api_response.tokens = {"token_field": "token_value"}

        # Expected parsed response
        expected_updated_field = {'skyflow_id': "12345", 'token_field': "token_value"}
        expected_response = UpdateResponse(updated_field=expected_updated_field)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_update_record.return_value = mock_api_response

        # Call the update function
        result = self.vault.update(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected UpdateResponse
        self.assertEqual(result.updated_field, expected_updated_field)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_update_request")
    def test_update_handles_generic_error(self, mock_validate):
        request = UpdateRequest(table="test_table", data={"skyflow_id": "123", "field": "value"},
                                return_tokens=False)
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_update_record.side_effect = Exception("Generic Exception")

        with self.assertRaises(Exception):
            self.vault.update(request)

        records_api.record_service_update_record.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_delete_request")
    @patch("skyflow.vault.controller._vault.parse_delete_response")
    def test_delete_successful(self, mock_parse_response, mock_validate):
        """Test delete functionality for a successful delete request."""

        # Mock request
        request = DeleteRequest(
            table=TABLE_NAME,
            ids=["12345", "67890"]
        )

        # Expected payload
        expected_payload = ["12345", "67890"]

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.record_id_response = ["12345", "67890"]

        # Expected parsed response
        expected_deleted_ids = ["12345", "67890"]
        expected_response = DeleteResponse(deleted_ids=expected_deleted_ids, errors=None)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_delete_record.return_value = mock_api_response

        # Call the delete function
        result = self.vault.delete(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected DeleteResponse
        self.assertEqual(result.deleted_ids, expected_deleted_ids)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_delete_request")
    def test_delete_handles_generic_exception(self, mock_validate):
        request = DeleteRequest(table="test_table", ids=["id1", "id2"])
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_delete_record.side_effect = Exception("Generic Error")

        with self.assertRaises(Exception):
            self.vault.delete(request)

        records_api.record_service_bulk_delete_record.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_get_request")
    @patch("skyflow.vault.controller._vault.parse_get_response")
    def test_get_successful(self, mock_parse_response, mock_validate):
        """Test get functionality for a successful get request."""

        # Mock request
        request = GetRequest(
            table=TABLE_NAME,
            ids=["12345", "67890"],
            redaction_type=RedactionType.PLAIN_TEXT,
            return_tokens=True,
            fields=["field1", "field2"],
            offset="0",
            limit="10",
            download_url=True,
            column_values=None
        )

        # Expected payload
        expected_payload = {
            "object_name": request.table,
            "skyflow_ids": request.ids,
            "redaction": request.redaction_type.value,
            "tokenization": request.return_tokens,
            "fields": request.fields,
            "offset": request.offset,
            "limit": request.limit,
            "download_url": request.download_url,
            "column_name": request.column_name,
            "column_values": request.column_values
        }

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(fields={"field1": "value1", "field2": "value2"}),
            Mock(fields={"field1": "value3", "field2": "value4"})
        ]

        # Expected parsed response
        expected_data = [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"}
        ]
        expected_response = GetResponse(data=expected_data, errors=None)

        # Set the return value for parse_get_response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_get_record.return_value = mock_api_response

        # Call the get function
        result = self.vault.get(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected GetResponse
        self.assertEqual(result.data, expected_data)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_get_request")
    @patch("skyflow.vault.controller._vault.parse_get_response")
    def test_get_successful_with_column_values(self, mock_parse_response, mock_validate):
        """Test get functionality for a successful get request."""

        # Mock request
        request = GetRequest(
            table=TABLE_NAME,
            redaction_type=RedactionType.PLAIN_TEXT,
            column_values=['customer+15@gmail.com'],
            column_name='email'
        )

        # Expected payload
        expected_payload = {
            "object_name": request.table,
            "tokenization": request.return_tokens,
            "column_name": request.column_name,
            "column_values": request.column_values
        }

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(fields={"field1": "value1", "field2": "value2"}),
            Mock(fields={"field1": "value3", "field2": "value4"})
        ]

        # Expected parsed response
        expected_data = [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"}
        ]
        expected_response = GetResponse(data=expected_data, errors=None)

        # Set the return value for parse_get_response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_get_record.return_value = mock_api_response

        # Call the get function
        result = self.vault.get(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_bulk_get_record.assert_called_once()

        # Check that the result matches the expected GetResponse
        self.assertEqual(result.data, expected_data)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_get_request")
    def test_get_handles_generic_error(self, mock_validate):
        request = GetRequest(table="test_table", ids=["id1", "id2"])
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_get_record.side_effect = Exception("Generic Exception")

        with self.assertRaises(Exception):
            self.vault.get(request)

        records_api.record_service_bulk_get_record.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_query_request")
    @patch("skyflow.vault.controller._vault.parse_query_response")
    def test_query_successful(self, mock_parse_response, mock_validate):
        """Test query functionality for a successful query request."""

        # Mock request
        request = QueryRequest(query="SELECT * FROM test_table")

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(fields={"field1": "value1", "field2": "value2"}),
            Mock(fields={"field1": "value3", "field2": "value4"})
        ]

        # Expected parsed response
        expected_fields = [
            {"field1": "value1", "field2": "value2", "tokenized_data": {}},
            {"field1": "value3", "field2": "value4", "tokenized_data": {}}
        ]
        expected_response = QueryResponse()
        expected_response.fields = expected_fields

        # Set the return value for parse_query_response
        mock_parse_response.return_value = expected_response
        query_api = self.vault_client.get_query_api.return_value
        query_api.query_service_execute_query.return_value = mock_api_response

        # Call the query function
        result = self.vault.query(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)

        # Check that the result matches the expected QueryResponse
        self.assertEqual(result.fields, expected_fields)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_query_request")
    def test_query_handles_generic_error(self, mock_validate):
        request = QueryRequest(query="SELECT * from table_name")
        query_api = self.vault_client.get_query_api.return_value
        query_api.query_service_execute_query.side_effect = Exception("Generic Exception")

        with self.assertRaises(Exception):
            self.vault.query(request)

        query_api.query_service_execute_query.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_detokenize_request")
    @patch("skyflow.vault.controller._vault.parse_detokenize_response")
    def test_detokenize_successful(self, mock_parse_response, mock_validate):
        request = DetokenizeRequest(
            data=[
                {
                    'token': 'token1',
                    'redaction': 'PLAIN_TEXT'
                },
                {
                    'token': 'token2',
                    'redaction': 'PLAIN_TEXT'
                }
            ],
            continue_on_error=False
        )

        expected_tokens_list = [
            V1DetokenizeRecordRequest(token="token1", redaction="PLAIN_TEXT"),
            V1DetokenizeRecordRequest(token="token2", redaction="PLAIN_TEXT")
        ]

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = {
            "records":[
                Mock(token="token1", value="value1", value_type=Mock(value="STRING"), error=None),
                Mock(token="token2", value="value2", value_type=Mock(value="STRING"), error=None)
            ]
        }

        # Expected parsed response
        expected_fields = [
            {"token": "token1", "value": "value1", "type": "STRING"},
            {"token": "token2", "value": "value2", "type": "STRING"}
        ]
        expected_response = DetokenizeResponse(detokenized_fields=expected_fields, errors=None)

        # Set the return value for parse_detokenize_response
        mock_parse_response.return_value = expected_response
        tokens_api = self.vault_client.get_tokens_api.return_value
        tokens_api.with_raw_response.record_service_detokenize.return_value = mock_api_response

        # Call the detokenize function
        result = self.vault.detokenize(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected DetokenizeResponse
        self.assertEqual(result.detokenized_fields, expected_fields)
        self.assertEqual(result.errors, None)  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_detokenize_request")
    def test_detokenize_handles_generic_error(self, mock_validate):
        request = DetokenizeRequest(
            data=[
                {
                    'token': 'token1',
                    'redaction': RedactionType.PLAIN_TEXT
                },
                {
                    'token': 'token2',
                    'redaction': RedactionType.PLAIN_TEXT
                }
            ],
            continue_on_error=False
        )
        tokens_api = self.vault_client.get_tokens_api.return_value
        tokens_api.record_service_detokenize.side_effect = Exception("Generic Error")

        with self.assertRaises(Exception):
            self.vault.detokenize(request)

        tokens_api.with_raw_response.record_service_detokenize.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_tokenize_request")
    @patch("skyflow.vault.controller._vault.parse_tokenize_response")
    def test_tokenize_successful(self, mock_parse_response, mock_validate):
        """Test tokenize functionality for a successful tokenize request."""

        # Mock request with tokenization parameters
        request = TokenizeRequest(
            values=[
                {"value": "value1", "column_group": "group1"},
                {"value": "value2", "column_group": "group2"}
            ]
        )

        expected_records_list = [
            V1TokenizeRecordRequest(value="value1", column_group="group1"),
            V1TokenizeRecordRequest(value="value2", column_group="group2")
        ]

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(token="token1"),
            Mock(token="token2")
        ]

        # Expected parsed response
        expected_fields = [
            {"token": "token1"},
            {"token": "token2"}
        ]
        expected_response = TokenizeResponse(tokenized_fields=expected_fields)

        # Set the return value for parse_tokenize_response
        mock_parse_response.return_value = expected_response
        tokens_api = self.vault_client.get_tokens_api.return_value
        tokens_api.record_service_tokenize.return_value = mock_api_response

        # Call the tokenize function
        result = self.vault.tokenize(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected TokenizeResponse
        self.assertEqual(result.tokenized_fields, expected_fields)

    @patch("skyflow.vault.controller._vault.validate_tokenize_request")
    def test_tokenize_handles_generic_error(self, mock_validate):
        request = TokenizeRequest(
            values=[
                {"value": "value1", "column_group": "group1"},
                {"value": "value2", "column_group": "group2"}
            ]
        )
        tokens_api = self.vault_client.get_tokens_api.return_value
        tokens_api.record_service_tokenize.side_effect = Exception("Generic Error")

        with self.assertRaises(Exception):
            self.vault.tokenize(request)

        tokens_api.record_service_tokenize.assert_called_once()

    @patch("skyflow.vault.controller._vault.validate_file_upload_request") 
    def test_upload_file_with_file_path_successful(self, mock_validate):
        """Test upload_file functionality using file path."""
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_path="/path/to/test.txt",
        )

        # Mock file open
        mocked_open = mock_open_func(read_data=b"test file content")
        
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = Mock(skyflow_id="123")

        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.upload_file_v_2.return_value = mock_api_response

        with patch('builtins.open', mocked_open):
            result = self.vault.upload_file(request)
            mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
            mocked_open.assert_called_once_with("/path/to/test.txt", "rb")
            self.assertEqual(result.skyflow_id, "123")
            self.assertIsNone(result.errors)

    @patch("skyflow.vault.controller._vault.validate_file_upload_request")
    def test_upload_file_with_base64_successful(self, mock_validate):
        """Test upload_file functionality using base64 content."""
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            base64="dGVzdCBmaWxlIGNvbnRlbnQ=",  # "test file content" in base64
            file_name="test.txt"
        )

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = Mock(skyflow_id="123")

        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.upload_file_v_2.return_value = mock_api_response

        # Call upload_file
        result = self.vault.upload_file(request)
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.assertEqual(result.skyflow_id, "123")
        self.assertIsNone(result.errors)

    @patch("skyflow.vault.controller._vault.validate_file_upload_request")
    def test_upload_file_with_file_object_successful(self, mock_validate):
        """Test upload_file functionality using file object."""
        
        # Create mock file object
        mock_file = Mock()
        mock_file.name = "test.txt"
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_object=mock_file
        )

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = Mock(skyflow_id="123")

        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.upload_file_v_2.return_value = mock_api_response

        # Call upload_file
        result = self.vault.upload_file(request)
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        self.assertEqual(result.skyflow_id, "123")
        self.assertIsNone(result.errors)

    @patch("skyflow.vault.controller._vault.validate_file_upload_request")
    def test_upload_file_handles_api_error(self, mock_validate):
        """Test upload_file error handling for API errors."""
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_path="/path/to/test.txt"
        )

        # Mock API error
        records_api = self.vault_client.get_records_api.return_value
        records_api.with_raw_response.upload_file_v_2.side_effect = Exception("Upload failed")

        # Assert that the exception is propagated
        with patch('builtins.open', mock_open(read_data=b"test content")):
            with self.assertRaises(Exception):
                self.vault.upload_file(request)
            mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)

    @patch("skyflow.vault.controller._vault.validate_file_upload_request")
    def test_upload_file_with_missing_file_source(self, mock_validate):
        """Test upload_file with no file source specified."""
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123"
        )

        mock_validate.side_effect = SkyflowError(SkyflowMessages.Error.MISSING_FILE_SOURCE.value, 
                                               SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

        with self.assertRaises(SkyflowError) as error:
            self.vault.upload_file(request)

        self.assertEqual(error.exception.message, SkyflowMessages.Error.MISSING_FILE_SOURCE.value)
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)

class TestFileUploadValidation(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()

    def test_validate_invalid_table(self):
        """Test validation fails when table is empty"""
        request = FileUploadRequest(
            table="",
            column_name="file_column", 
            skyflow_id="123",
            file_path="/path/to/file.txt"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.EMPTY_TABLE_VALUE.value)

    def test_validate_empty_skyflow_id(self):
        """Test validation fails when skyflow_id is empty"""
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="",
            file_path="/path/to/file.txt"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)

    def test_validate_invalid_column_name(self):
        """Test validation fails when column_name is missing"""
        request = FileUploadRequest(
            table="test_table",
            skyflow_id="123",
            column_name="",
            file_path="/path/to/file.txt"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, 
                        SkyflowMessages.Error.INVALID_FILE_COLUMN_NAME.value.format("FILE_UPLOAD"))


    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_validate_file_path_success(self, mock_isfile, mock_exists):
        """Test validation succeeds with valid file path"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_path="/path/to/file.txt"
        )
        validate_file_upload_request(self.logger, request)
        mock_exists.assert_called_once_with("/path/to/file.txt")
        mock_isfile.assert_called_once_with("/path/to/file.txt")

    @patch('os.path.exists')
    def test_validate_invalid_file_path(self, mock_exists):
        """Test validation fails with invalid file path"""
        mock_exists.return_value = False
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_path="/invalid/path.txt"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.INVALID_FILE_PATH.value)

    def test_validate_base64_success(self):
        """Test validation succeeds with valid base64"""
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            base64="dGVzdCBmaWxlIGNvbnRlbnQ=",
            file_name="test.txt"
        )
        validate_file_upload_request(self.logger, request)

    def test_validate_base64_without_filename(self):
        """Test validation fails with base64 but no filename"""
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            base64="dGVzdCBmaWxlIGNvbnRlbnQ="
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.INVALID_FILE_NAME.value)

    def test_validate_invalid_base64(self):
        """Test validation fails with invalid base64"""
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            base64="invalid-base64",
            file_name="test.txt"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.INVALID_BASE64_STRING.value)

    def test_validate_file_object_success(self):
        """Test validation succeeds with valid file object"""
        mock_file = Mock()
        mock_file.seek = Mock()  # Add seek method
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_object=mock_file
        )
        validate_file_upload_request(self.logger, request)

    def test_validate_invalid_file_object(self):
        """Test validation fails with invalid file object"""
        mock_file = Mock()
        mock_file.seek = Mock(side_effect=Exception())  # Make seek fail
        
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123",
            file_object=mock_file
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.INVALID_FILE_OBJECT.value)

    def test_validate_missing_file_source(self):
        """Test validation fails when no file source is provided"""
        request = FileUploadRequest(
            table="test_table",
            column_name="file_column",
            skyflow_id="123"
        )
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.MISSING_FILE_SOURCE.value)
        with self.assertRaises(SkyflowError) as error:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(error.exception.message, SkyflowMessages.Error.MISSING_FILE_SOURCE.value)
