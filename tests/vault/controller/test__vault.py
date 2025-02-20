import unittest
from unittest.mock import Mock, patch
from skyflow.generated.rest import RecordServiceBatchOperationBody, V1BatchRecord, RecordServiceInsertRecordBody, \
    V1FieldRecords, RecordServiceUpdateRecordBody, RecordServiceBulkDeleteRecordBody, QueryServiceExecuteQueryBody, \
    V1DetokenizeRecordRequest, V1DetokenizePayload, V1TokenizePayload, V1TokenizeRecordRequest, RedactionEnumREDACTION, \
    BatchRecordMethod
from skyflow.utils.enums import RedactionType, TokenMode
from skyflow.vault.controller import Vault
from skyflow.vault.data import InsertRequest, InsertResponse, UpdateResponse, UpdateRequest, DeleteResponse, \
    DeleteRequest, GetRequest, GetResponse, QueryRequest, QueryResponse
from skyflow.vault.tokens import DetokenizeRequest, DetokenizeResponse, TokenizeResponse, TokenizeRequest

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
            table_name=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=None,
            return_tokens=True,
            upsert='column_name',
            continue_on_error=True
        )

        expected_body = RecordServiceBatchOperationBody(
            records=[
                V1BatchRecord(
                    fields={"field": "value"},
                    table_name=TABLE_NAME,
                    method=BatchRecordMethod.POST,
                    tokenization=True,
                    upsert="column_name"
                )
            ],
            continue_on_error=True,
            byot="DISABLE"
        )

        # Mock API response to contain a mix of successful and failed insertions
        mock_api_response = Mock()
        mock_api_response.responses = [
            {"Status": 200, "Body": {"records": [{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]}},
            {"Status": 400, "Body": {"error": "Insert error for record 2"}}
        ]

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
        records_api.record_service_batch_operation_with_http_info.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_batch_operation_with_http_info.assert_called_once_with(VAULT_ID, expected_body)
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
            table_name=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=None,
            return_tokens=True,
            upsert=None,
            homogeneous=True,
            continue_on_error=False
        )

        # Expected API request body based on InsertRequest parameters
        expected_body = RecordServiceInsertRecordBody(
            records=[
                V1FieldRecords(fields={"field": "value"})
            ],
            tokenization=True,
            upsert=None,
            homogeneous=True
        )

        # Mock API response for a successful insert
        mock_api_response = Mock()
        mock_api_response.records = [{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]

        # Expected parsed response
        expected_inserted_fields = [{'skyflow_id': 'id1', 'token_field': 'token_val1'}]
        expected_response = InsertResponse(inserted_fields=expected_inserted_fields)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_insert_record.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_insert_record.assert_called_once_with(VAULT_ID, TABLE_NAME,
                                                                         expected_body)
        mock_parse_response.assert_called_once_with(mock_api_response, False)

        # Assert that the result matches the expected InsertResponse
        self.assertEqual(result.inserted_fields, expected_inserted_fields)
        self.assertEqual(result.errors, [])  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_insert_request")
    @patch("skyflow.vault.controller._vault.parse_insert_response")
    def test_insert_with_continue_on_error_false_when_tokens_are_not_none(self, mock_parse_response, mock_validate):
        """Test insert functionality when continue_on_error is False, ensuring a single bulk insert."""

        # Mock request with continue_on_error set to False
        request = InsertRequest(
            table_name=TABLE_NAME,
            values=[{"field": "value"}],
            tokens=[{"token_field": "token_val1"}],
            return_tokens=True,
            upsert=None,
            homogeneous=True,
            continue_on_error=False
        )

        # Expected API request body based on InsertRequest parameters
        expected_body = RecordServiceInsertRecordBody(
            records=[
                V1FieldRecords(fields={"field": "value"}, tokens={"token_field": "token_val1"})
            ],
            tokenization=True,
            upsert=None,
            homogeneous=True
        )

        # Mock API response for a successful insert
        mock_api_response = Mock()
        mock_api_response.records = [{"skyflow_id": "id1", "tokens": {"token_field": "token_val1"}}]

        # Expected parsed response
        expected_inserted_fields = [{'skyflow_id': 'id1', 'token_field': 'token_val1'}]
        expected_response = InsertResponse(inserted_fields=expected_inserted_fields)

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_insert_record.return_value = mock_api_response

        # Call the insert function
        result = self.vault.insert(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_insert_record.assert_called_once_with(VAULT_ID, TABLE_NAME,
                                                                         expected_body)
        mock_parse_response.assert_called_once_with(mock_api_response, False)

        # Assert that the result matches the expected InsertResponse
        self.assertEqual(result.inserted_fields, expected_inserted_fields)
        self.assertEqual(result.errors, [])  # No errors expected

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
        expected_payload = RecordServiceUpdateRecordBody(
            record=V1FieldRecords(
                fields={"field": "new_value"},
                tokens=request.tokens
            ),
            tokenization=request.return_tokens,
            byot=request.token_mode.value
        )

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
        records_api.record_service_update_record.assert_called_once_with(
            VAULT_ID,
            request.table,
            request.data["skyflow_id"],
            expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected UpdateResponse
        self.assertEqual(result.updated_field, expected_updated_field)
        self.assertEqual(result.errors, [])  # No errors expected

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
        expected_payload = RecordServiceBulkDeleteRecordBody(skyflow_ids=request.ids)

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.record_id_response = ["12345", "67890"]

        # Expected parsed response
        expected_deleted_ids = ["12345", "67890"]
        expected_response = DeleteResponse(deleted_ids=expected_deleted_ids, errors=[])

        # Set the return value for the parse response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_delete_record.return_value = mock_api_response

        # Call the delete function
        result = self.vault.delete(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_bulk_delete_record.assert_called_once_with(
            VAULT_ID,
            request.table,
            expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected DeleteResponse
        self.assertEqual(result.deleted_ids, expected_deleted_ids)
        self.assertEqual(result.errors, [])  # No errors expected

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
        expected_response = GetResponse(data=expected_data, errors=[])

        # Set the return value for parse_get_response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_get_record.return_value = mock_api_response

        # Call the get function
        result = self.vault.get(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_bulk_get_record.assert_called_once_with(
            VAULT_ID,
            **expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected GetResponse
        self.assertEqual(result.data, expected_data)
        self.assertEqual(result.errors, [])  # No errors expected

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
        expected_response = GetResponse(data=expected_data, errors=[])

        # Set the return value for parse_get_response
        mock_parse_response.return_value = expected_response
        records_api = self.vault_client.get_records_api.return_value
        records_api.record_service_bulk_get_record.return_value = mock_api_response

        # Call the get function
        result = self.vault.get(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        records_api.record_service_bulk_get_record.assert_called_once()
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected GetResponse
        self.assertEqual(result.data, expected_data)
        self.assertEqual(result.errors, [])  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_query_request")
    @patch("skyflow.vault.controller._vault.parse_query_response")
    def test_query_successful(self, mock_parse_response, mock_validate):
        """Test query functionality for a successful query request."""

        # Mock request
        request = QueryRequest(query="SELECT * FROM test_table")

        # Expected payload as a QueryServiceExecuteQueryBody instance
        expected_payload = QueryServiceExecuteQueryBody(query=request.query)

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
        query_api.query_service_execute_query.assert_called_once_with(
            VAULT_ID,
            expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected QueryResponse
        self.assertEqual(result.fields, expected_fields)
        self.assertEqual(result.errors, [])  # No errors expected

    @patch("skyflow.vault.controller._vault.validate_detokenize_request")
    @patch("skyflow.vault.controller._vault.parse_detokenize_response")
    def test_detokenize_successful(self, mock_parse_response, mock_validate):
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

        # Expected payload as a V1DetokenizePayload instance
        tokens_list = [
            V1DetokenizeRecordRequest(token="token1", redaction=RedactionEnumREDACTION.PLAIN_TEXT),
            V1DetokenizeRecordRequest(token="token2", redaction=RedactionEnumREDACTION.PLAIN_TEXT)
        ]
        expected_payload = V1DetokenizePayload(
            detokenization_parameters=tokens_list,
            continue_on_error=request.continue_on_error
        )

        # Mock API response
        mock_api_response = Mock()
        mock_api_response.records = [
            Mock(skyflow_id="id_1", token="token1", value="value1", value_type=Mock(value="STRING"), error=None),
            Mock(skyflow_id="id_2", token="token2", value="value2", value_type=Mock(value="STRING"), error=None)
        ]

        # Expected parsed response
        expected_fields = [
            {"skyflow_id": "id_1", "token": "token1", "value": "value1", "type": "STRING"},
            {"skyflow_id": "id_2", "token": "token2", "value": "value2", "type": "STRING"}
        ]
        expected_response = DetokenizeResponse(detokenized_fields=expected_fields, errors=[])

        # Set the return value for parse_detokenize_response
        mock_parse_response.return_value = expected_response
        tokens_api = self.vault_client.get_tokens_api.return_value
        tokens_api.record_service_detokenize_with_http_info.return_value = mock_api_response

        # Call the detokenize function
        result = self.vault.detokenize(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        tokens_api.record_service_detokenize_with_http_info.assert_called_once_with(
            VAULT_ID,
            detokenize_payload=expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected DetokenizeResponse
        self.assertEqual(result.detokenized_fields, expected_fields)
        self.assertEqual(result.errors, [])  # No errors expected

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

        # Expected payload as a V1TokenizePayload instance
        records_list = [
            V1TokenizeRecordRequest(value="value1", column_group="group1"),
            V1TokenizeRecordRequest(value="value2", column_group="group2")
        ]
        expected_payload = V1TokenizePayload(tokenization_parameters=records_list)

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
        tokens_api.record_service_tokenize.assert_called_once_with(
            VAULT_ID,
            tokenize_payload=expected_payload
        )
        mock_parse_response.assert_called_once_with(mock_api_response)

        # Check that the result matches the expected TokenizeResponse
        self.assertEqual(result.tokenized_fields, expected_fields)