import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from skyflow.error import SkyflowError
from skyflow.utils.validations._validations import (
    validate_required_field, validate_api_key, validate_credentials,
    validate_log_level, validate_keys, validate_vault_config,
    validate_update_vault_config, validate_connection_config,
    validate_update_connection_config, validate_file_from_request,
    validate_insert_request, validate_delete_request, validate_query_request,
    validate_get_detect_run_request, validate_get_request, validate_update_request,
    validate_detokenize_request, validate_tokenize_request, validate_invoke_connection_params,
    validate_deidentify_text_request, validate_reidentify_text_request, validate_deidentify_file_request,
    validate_file_upload_request
)
from skyflow.utils import SkyflowMessages
from skyflow.utils.enums import DetectEntities, RedactionType
from skyflow.vault.data import GetRequest, UpdateRequest
from skyflow.vault.detect import DeidentifyTextRequest, Transformations, DateTransformation, ReidentifyTextRequest, \
    FileInput, DeidentifyFileRequest, Bleep
from skyflow.vault.data._file_upload_request import FileUploadRequest
from skyflow.vault.tokens import DetokenizeRequest
from skyflow.vault.connection._invoke_connection_request import InvokeConnectionRequest

class TestValidations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file = tempfile.NamedTemporaryFile(delete=False)
        cls.temp_file.write(b"test content")
        cls.temp_file.close()
        cls.temp_file_path = cls.temp_file.name
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.temp_dir_path = cls.temp_dir.name

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_file_path):
            os.unlink(cls.temp_file_path)
        cls.temp_dir.cleanup()

    def setUp(self):
        self.logger = Mock()

    def test_validate_required_field_valid(self):
        config = {"test_field": "test_value"}
        validate_required_field(
            self.logger, 
            config, 
            "test_field", 
            str,
            "Empty error",
            "Invalid error"
        )

    def test_validate_required_field_missing(self):
        config = {}
        with self.assertRaises(SkyflowError) as context:
            validate_required_field(
                self.logger,
                config,
                "vault_id",
                str,
                "Empty error",
                "Invalid error"
            )
        self.assertEqual(context.exception.message, "Invalid error")

    def test_validate_required_field_empty_string(self):
        config = {"test_field": ""}
        with self.assertRaises(SkyflowError) as context:
            validate_required_field(
                self.logger,
                config,
                "test_field",
                str,
                "Empty error",
                "Invalid error"
            )
        self.assertEqual(context.exception.message, "Empty error")

    def test_validate_required_field_wrong_type(self):
        config = {"test_field": 123}
        with self.assertRaises(SkyflowError) as context:
            validate_required_field(
                self.logger,
                config,
                "test_field",
                str,
                "Empty error",
                "Invalid error"
            )
        self.assertEqual(context.exception.message, "Invalid error")

    def test_validate_api_key_valid(self):
        valid_key = "sky-abc12-1234567890abcdef1234567890abcdef"
        self.assertTrue(validate_api_key(valid_key, self.logger))

    def test_validate_api_key_invalid_prefix(self):
        invalid_key = "invalid-abc12-1234567890abcdef1234567890abcdef"
        self.assertFalse(validate_api_key(invalid_key, self.logger))

    def test_validate_api_key_invalid_length(self):
        invalid_key = "sky-abc12-123456"
        self.assertFalse(validate_api_key(invalid_key, self.logger))

    def test_validate_credentials_with_api_key(self):
        credentials = {
            "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
        }
        validate_credentials(self.logger, credentials)

    def test_validate_credentials_with_expired_token(self):
        credentials = {
            "token": "expired_token"
        }
        with patch('skyflow.service_account.is_expired', return_value=True):
            with self.assertRaises(SkyflowError) as context:
                validate_credentials(self.logger, credentials)
            self.assertEqual(context.exception.message, SkyflowMessages.Error.EXPIRED_BEARER_TOKEN.value)

    def test_validate_credentials_empty_credentials(self):
        credentials = {}
        with self.assertRaises(SkyflowError) as context:
            validate_credentials(self.logger, credentials)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CREDENTIALS.value)

    def test_validate_credentials_multiple_auth_methods(self):
        credentials = {
            "token": "valid_token",
            "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
        }
        with self.assertRaises(SkyflowError) as context:
            validate_credentials(self.logger, credentials)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MULTIPLE_CREDENTIALS_PASSED.value)


    def test_validate_credentials_with_empty_context(self):
        credentials = {
            "token": "valid_token",
            "context": ""
        }
        with patch('skyflow.service_account.is_expired', return_value=False):
            with self.assertRaises(SkyflowError) as context:
                validate_credentials(self.logger, credentials)
            self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_CONTEXT.value)
            
    def test_validate_log_level_valid(self):
        from skyflow.utils.enums import LogLevel
        log_level = LogLevel.ERROR
        validate_log_level(self.logger, log_level)

    def test_validate_log_level_invalid(self):
        class InvalidEnum:
            pass
        invalid_log_level = InvalidEnum()
        with self.assertRaises(SkyflowError) as context:
            validate_log_level(self.logger, invalid_log_level)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_LOG_LEVEL.value)

    def test_validate_log_level_none(self):
        with self.assertRaises(SkyflowError) as context:
            validate_log_level(self.logger, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_LOG_LEVEL.value)

    def test_validate_keys_valid(self):
        config = {"vault_id": "test_id", "cluster_id": "test_cluster"}
        validate_keys(self.logger, config, ["vault_id", "cluster_id"])

    def test_validate_keys_invalid(self):
        config = {"invalid_key": "value"}
        with self.assertRaises(SkyflowError) as context:
            validate_keys(self.logger, config, ["vault_id", "cluster_id"])
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_KEY.value.format("invalid_key"))

    def test_validate_vault_config_valid(self):
        from skyflow.utils.enums import Env
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            },
            "env": Env.DEV
        }
        self.assertTrue(validate_vault_config(self.logger, config))

    def test_validate_vault_config_missing_required(self):
        config = {
            "cluster_id": "cluster123"
        }
        with self.assertRaises(SkyflowError) as context:
            validate_vault_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_VAULT_ID.value)


    def test_validate_update_vault_config_valid(self):
        from skyflow.utils.enums import Env
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            },
            "env": Env.DEV
        }
        self.assertTrue(validate_update_vault_config(self.logger, config))

    def test_validate_update_vault_config_invalid_cluster_id(self):
        config = {
            "vault_id": "vault123",
            "cluster_id": "",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_vault_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format("vault123"))

    def test_validate_update_vault_config_missing_credentials(self):
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_vault_config(self.logger, config)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("vault", "vault123")
        )

    def test_validate_connection_config_valid(self):
        config = {
            "connection_id": "conn123",
            "connection_url": "https://example.com",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        self.assertTrue(validate_connection_config(self.logger, config))

    def test_validate_connection_config_missing_url(self):
        config = {
            "connection_id": "conn123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_connection_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CONNECTION_URL.value.format("conn123"))

    def test_validate_connection_config_empty_connection_id(self):
        config = {
            "connection_id": "",
            "connection_url": "https://example.com",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_connection_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_CONNECTION_ID.value)

    def test_validate_connection_config_missing_credentials(self):
        config = {
            "connection_id": "conn123",
            "connection_url": "https://example.com",
        }
        with self.assertRaises(SkyflowError) as context:
            validate_connection_config(self.logger, config)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("connection", "conn123")
        )

    def test_validate_update_connection_config_valid(self):
        config = {
            "connection_id": "conn123",
            "connection_url": "https://example.com",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        self.assertTrue(validate_update_connection_config(self.logger, config))

    def test_validate_update_connection_config_missing_credentials(self):
        config = {
            "connection_id": "conn123",
            "connection_url": "https://example.com"
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_connection_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_CREDENTIALS.value.format("connection", "conn123"))

    def test_validate_update_connection_config_empty_url(self):
        config = {
            "connection_id": "conn123",
            "connection_url": "",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef"
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_connection_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_CONNECTION_URL.value.format("conn123"))

    def test_validate_file_from_request_valid_file(self):
        file_obj = MagicMock()
        file_obj.name = "test.txt"
        file_input = MagicMock()
        file_input.file = file_obj
        file_input.file_path = None
        validate_file_from_request(file_input)

    def test_validate_file_from_request_valid_file_path(self):
        file_input = MagicMock()
        file_input.file = None
        file_input.file_path = self.temp_file_path
        validate_file_from_request(file_input)

    def test_validate_file_from_request_missing_both(self):
        file_input = MagicMock()
        file_input.file = None
        file_input.file_path = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_DEIDENTIFY_FILE_INPUT.value)

    def test_validate_file_from_request_both_provided(self):
        file_obj = MagicMock()
        file_obj.name = "test.txt"
        file_input = MagicMock()
        file_input.file = file_obj
        file_input.file_path = "/path/to/file"
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_DEIDENTIFY_FILE_INPUT.value)


    def test_validate_file_from_request_invalid_file_path(self):
        file_input = MagicMock()
        file_input.file = None
        file_input.file_path = "/nonexistent/path/to/file"
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_DEIDENTIFY_FILE_PATH.value)

    def test_validate_insert_request_valid(self):
        request = MagicMock()
        request.table = "test_table"
        request.values = [{"field1": "value1"}]
        request.upsert = None
        request.homogeneous = None
        request.token_mode = None
        request.return_tokens = False
        request.continue_on_error = False
        request.tokens = None
        validate_insert_request(self.logger, request)

    def test_validate_insert_request_invalid_table(self):
        request = MagicMock()
        request.table = 123
        request.values = [{"field1": "value1"}]
        with self.assertRaises(SkyflowError) as context:
            validate_insert_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TABLE_NAME_IN_INSERT.value)

    def test_validate_insert_request_empty_values(self):
        request = MagicMock()
        request.table = "test_table"
        request.values = []
        with self.assertRaises(SkyflowError) as context:
            validate_insert_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_DATA_IN_INSERT.value)


    def test_validate_delete_request_valid(self):
        request = MagicMock()
        request.table = "test_table"
        request.ids = ["id1", "id2"]
        validate_delete_request(self.logger, request)

    def test_validate_delete_request_empty_table(self):
        request = MagicMock()
        request.table = ""
        request.ids = ["id1"]
        with self.assertRaises(SkyflowError) as context:
            validate_delete_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TABLE_VALUE.value)

    def test_validate_delete_request_missing_ids(self):
        request = MagicMock()
        request.table = "test_table"
        request.ids = None
        with self.assertRaises(SkyflowError) as context:
            validate_delete_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_RECORD_IDS_IN_DELETE.value)

    def test_validate_query_request_valid(self):
        request = MagicMock()
        request.query = "SELECT * FROM test_table"
        validate_query_request(self.logger, request)

    def test_validate_query_request_empty_query(self):
        request = MagicMock()
        request.query = ""
        with self.assertRaises(SkyflowError) as context:
            validate_query_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_QUERY.value)

    def test_validate_query_request_invalid_query_type(self):
        request = MagicMock()
        request.query = 123
        with self.assertRaises(SkyflowError) as context:
            validate_query_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_QUERY_TYPE.value.format(str(type(123))))

    def test_validate_query_request_non_select_query(self):
        request = MagicMock()
        request.query = "INSERT INTO test_table VALUES (1)"
        with self.assertRaises(SkyflowError) as context:
            validate_query_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_QUERY_COMMAND.value.format(request.query))

    def test_validate_get_detect_run_request_valid(self):
        request = MagicMock()
        request.run_id = "test_run_123"
        validate_get_detect_run_request(self.logger, request)

    def test_validate_get_detect_run_request_empty_run_id(self):
        request = MagicMock()
        request.run_id = ""
        with self.assertRaises(SkyflowError) as context:
            validate_get_detect_run_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_RUN_ID.value)

    def test_validate_get_detect_run_request_invalid_run_id_type(self):
        request = MagicMock()
        request.run_id = 123  # Invalid type
        with self.assertRaises(SkyflowError) as context:
            validate_get_detect_run_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_RUN_ID.value)
        
    def test_validate_get_request_valid(self):
        from skyflow.utils.enums import RedactionType
        request = MagicMock()
        request.table = "test_table"
        request.redaction_type = RedactionType.PLAIN_TEXT
        request.column_name = None
        request.column_values = None
        request.ids = ["id1", "id2"]
        request.fields = ["field1", "field2"]
        request.offset = None
        request.limit = None
        request.download_url = False
        request.return_tokens = False
        validate_get_request(self.logger, request)
        

    def test_validate_get_request_invalid_table_type(self):
        request = MagicMock()
        request.table = 123
        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TABLE_VALUE.value)

    def test_validate_get_request_empty_table(self):
        request = MagicMock()
        request.table = ""
        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TABLE_VALUE.value)

    def test_validate_get_request_invalid_redaction_type(self):
        request = GetRequest(
            table="test_table",
            fields="invalid",
            ids=["id1", "id2"],
            redaction_type="invalid"
        )

        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(type(request.redaction_type)))

    def test_validate_get_request_invalid_fields_type(self):
        request= GetRequest(
            table="test_table",
            fields="invalid"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_FIELDS_VALUE.value.format(type(request.fields)))

    def test_validate_get_request_empty_fields(self):
        request = GetRequest(
            table="test_table",
            ids=[],
            fields=[]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_FIELDS_VALUE.value.format(type(request.fields)))
        
    def test_validate_get_request_invalid_column_values_type(self):
        request = GetRequest(
            table="test_table",
            column_name="test_column",
            column_values="invalid",
        )

        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_COLUMN_VALUE.value.format(type(request.column_values)))

    def test_validate_get_request_tokens_with_redaction(self):
        request = GetRequest(
            table="test_table",
            return_tokens=True,
            redaction_type = RedactionType.PLAIN_TEXT
        )

        with self.assertRaises(SkyflowError) as context:
            validate_get_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.REDACTION_WITH_TOKENS_NOT_SUPPORTED.value)

    def test_validate_query_request_valid_complex(self):
        request = MagicMock()
        request.query = "SELECT * FROM table1 JOIN table2 ON table1.id = table2.id WHERE field = 'value'"
        validate_query_request(self.logger, request)
        

    def test_validate_query_request_invalid_update(self):
        request = MagicMock()
        request.query = "UPDATE table SET field = 'value'"  # Only SELECT allowed
        with self.assertRaises(SkyflowError) as context:
            validate_query_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_QUERY_COMMAND.value.format(request.query))

    def test_validate_update_request_valid(self):
        request = MagicMock()
        request.table = "test_table"
        request.data = {"skyflow_id": "id123", "field1": "value1"}
        request.return_tokens = False
        request.token_mode = None
        request.tokens = None
        validate_update_request(self.logger, request)

    def test_validate_update_request_invalid_table_type(self):
        request = UpdateRequest(
            table=123,
             data = {"skyflow_id": "id123"}
        )
        with self.assertRaises(SkyflowError) as context:
            validate_update_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TABLE_VALUE.value)

    def test_validate_update_request_invalid_token_mode(self):
        request = UpdateRequest(
            table="test_table",
            data = {"skyflow_id": "id123", "field1": "value1"},
            token_mode = "invalid"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_update_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_MODE_TYPE.value)

    def test_validate_detokenize_request_valid(self):
        request = MagicMock()
        request.data = [{"token": "token123"}]
        request.continue_on_error = False
        validate_detokenize_request(self.logger, request)
        
    def test_validate_detokenize_request_empty_data(self):
        request = MagicMock()
        request.data = []  # Empty list
        request.continue_on_error = False
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TOKENS_LIST_VALUE.value)

    def test_validate_detokenize_request_invalid_token(self):
        request = MagicMock()
        request.data = [{"token": 123}]  # Invalid token type
        request.continue_on_error = False
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, 
            SkyflowMessages.Error.INVALID_TOKEN_TYPE.value.format("DETOKENIZE"))

    def test_validate_tokenize_request_valid(self):
        request = MagicMock()
        request.values = [{"value": "test", "column_group": "group1"}]
        validate_tokenize_request(self.logger, request)
        

    def test_validate_tokenize_request_invalid_values_type(self):
        request = MagicMock()
        request.values = "invalid"  # Should be list
        with self.assertRaises(SkyflowError) as context:
            validate_tokenize_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETERS.value.format(type(request.values)))

    def test_validate_tokenize_request_empty_values(self):
        request = MagicMock()
        request.values = []  # Empty list
        with self.assertRaises(SkyflowError) as context:
            validate_tokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TOKENIZE_PARAMETERS.value)

    def test_validate_tokenize_request_missing_required_fields(self):
        request = MagicMock()
        request.values = [{"value": "test"}]  # Missing column_group
        with self.assertRaises(SkyflowError) as context:
            validate_tokenize_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TOKENIZE_PARAMETER_KEY.value.format(0))

    def test_validate_invoke_connection_params_valid(self):
        query_params = {"param1": "value1"}
        path_params = {"path1": "value1"}
        validate_invoke_connection_params(self.logger, query_params, path_params)
        
    def test_validate_invoke_connection_params_invalid_path_params_type(self):
        request = InvokeConnectionRequest(
            method="GET",
            query_params={"param1": "value1"},
            path_params="invalid"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_invoke_connection_params(self.logger, request.query_params, request.path_params)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_PATH_PARAMS.value)

    def test_validate_invoke_connection_params_invalid_query_params_type(self):
        request = InvokeConnectionRequest(
            method="GET",
            query_params="invalid",
            path_params={"path1": "value1"}
        )
        with self.assertRaises(SkyflowError) as context:
            validate_invoke_connection_params(self.logger, request.query_params, request.path_params)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_QUERY_PARAMS.value)

    def test_validate_invoke_connection_params_non_string_path_param(self):
        request = InvokeConnectionRequest(
            method="GET",
            query_params={"param1": "value1"},
            path_params={1: "value1"}
        )
        with self.assertRaises(SkyflowError) as context:
            validate_invoke_connection_params(self.logger, request.query_params, request.path_params)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_PATH_PARAMS.value)

    def test_validate_invoke_connection_params_non_string_query_param_key(self):
        request = InvokeConnectionRequest(
            method="GET",
            query_params={1: "value1"},
            path_params={"path1": "value1"}
        )
        with self.assertRaises(SkyflowError) as context:
            validate_invoke_connection_params(self.logger, request.query_params, request.path_params)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_QUERY_PARAMS.value)

    def test_validate_invoke_connection_params_non_serializable_query_params(self):
        class NonSerializable:
            pass
        request = InvokeConnectionRequest(
            method="GET",
            query_params={"param1": NonSerializable()},
            path_params={"path1": "value1"}
        )
        with self.assertRaises(SkyflowError) as context:
            validate_invoke_connection_params(self.logger, request.query_params, request.path_params)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_QUERY_PARAMS.value)

    def test_validate_deidentify_text_request_valid(self):
        request = DeidentifyTextRequest(
            text="test",
            entities=None,
            allow_regex_list=None,
            restrict_regex_list = None,
            token_format = None,
            transformations = None,
        )
        validate_deidentify_text_request(self.logger, request)

    def test_validate_reidentify_text_request_valid(self):
        request = ReidentifyTextRequest(
            text="test",
            masked_entities=[DetectEntities.CREDIT_CARD],
            redacted_entities=[DetectEntities.SSN],
            plain_text_entities=None,
        )
        validate_reidentify_text_request(self.logger, request)

    def test_validate_reidentify_text_request_empty_text(self):
        request = ReidentifyTextRequest(
            text="",
            masked_entities=[DetectEntities.CREDIT_CARD],
            redacted_entities=[DetectEntities.SSN],
        )
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TEXT_IN_REIDENTIFY.value)

    def test_validate_reidentify_text_request_invalid_redacted_entities(self):
        request = ReidentifyTextRequest(
            text="test",
            redacted_entities="invalid",
        )
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_REDACTED_ENTITIES_IN_REIDENTIFY.value)

    def test_validate_reidentify_text_request_invalid_plain_text_entities(self):
        request = ReidentifyTextRequest(
            text="test",
            plain_text_entities="invalid",
        )
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_PLAIN_TEXT_ENTITIES_IN_REIDENTIFY.value)


    def test_validate_deidentify_text_request_empty_text(self):
        request = DeidentifyTextRequest(
            text="",
            entities=None,
            allow_regex_list=None,
            restrict_regex_list=None,
            token_format=None,
            transformations=None,
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TEXT_IN_DEIDENTIFY.value)

    def test_validate_deidentify_text_request_invalid_text_type(self):
        request = DeidentifyTextRequest(
            text=["test"],
            entities=None,
            allow_regex_list=None,
            restrict_regex_list=None,
            token_format=None,
            transformations=None,
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TEXT_IN_DEIDENTIFY.value)

    def test_validate_deidentify_text_request_invalid_entities_type(self):
        request = DeidentifyTextRequest(
            text="test",
            entities="invalid",
            allow_regex_list=None,
            restrict_regex_list=None,
            token_format=None,
            transformations=None,
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_ENTITIES_IN_DEIDENTIFY.value)

    def test_validate_deidentify_text_request_invalid_allow_regex(self):
        request = DeidentifyTextRequest(
            text="test",
            allow_regex_list="invalid",
            restrict_regex_list=None,
            token_format=None,
            transformations=None,
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_ALLOW_REGEX_LIST.value)

    def test_validate_deidentify_text_request_invalid_restrict_regex(self):
        request = DeidentifyTextRequest(
            text="test",
            restrict_regex_list="invalid",
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_RESTRICT_REGEX_LIST.value)

    def test_validate_deidentify_text_request_invalid_token_format(self):
        request = DeidentifyTextRequest(
            text="test",
            token_format="invalid",
            transformations=None,
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TOKEN_FORMAT.value)


    def test_validate_reidentify_text_request_valid(self):
        request = MagicMock()
        request.text = "test text"
        request.redacted_entities = None 
        request.masked_entities = None
        request.plain_text_entities = None
        validate_reidentify_text_request(self.logger, request)

    def test_validate_reidentify_text_request_empty_text(self):
        request = MagicMock()
        request.text = ""  # Empty text
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TEXT_IN_REIDENTIFY.value)

    def test_validate_reidentify_text_request_invalid_text_type(self):
        request = MagicMock()
        request.text = 123  # Invalid type
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_TEXT_IN_REIDENTIFY.value)

    def test_validate_reidentify_text_request_invalid_redacted_entities(self):
        request = MagicMock()
        request.text = "test text"
        request.redacted_entities = "invalid"
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_REDACTED_ENTITIES_IN_REIDENTIFY.value)

    def test_validate_reidentify_text_request_invalid_plain_text_entities(self):
        request = ReidentifyTextRequest(
            text="test text",
            plain_text_entities="invalid"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_PLAIN_TEXT_ENTITIES_IN_REIDENTIFY.value)

    def test_validate_deidentify_file_request_valid(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            entities=None,
            allow_regex_list=None,
            restrict_regex_list=None,
            token_format=None,
            transformations=None,
            output_processed_image=None,
            output_ocr_text=None,
            masking_method=None,
            pixel_density=None,
            max_resolution=None,
            output_processed_audio=None,
            output_transcription=None,
            bleep=None,
            output_directory=None,
            wait_time=None
        )
        validate_deidentify_file_request(self.logger, request)

    def test_validate_deidentify_file_request_missing_file(self):
        request = DeidentifyFileRequest(file=None)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_INPUT.value)

    def test_validate_deidentify_file_request_invalid_entities(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            entities="invalid"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_DETECT_ENTITIES_TYPE.value)

    def test_validate_deidentify_file_request_invalid_allow_regex(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            allow_regex_list="invalid",
            entities=[DetectEntities.ACCOUNT_NUMBER]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_ALLOW_REGEX_LIST.value)

    def test_validate_deidentify_file_request_invalid_restrict_regex(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            restrict_regex_list="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_RESTRICT_REGEX_LIST.value)

    def test_validate_deidentify_file_request_invalid_token_format(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            token_format="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_FORMAT.value)

    def test_validate_deidentify_file_request_invalid_transformations(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            transformations="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TRANSFORMATIONS.value)

    def test_validate_deidentify_file_request_invalid_output_processed_image(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            output_processed_image="true",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_OUTPUT_PROCESSED_IMAGE.value)

    def test_validate_deidentify_file_request_invalid_output_ocr_text(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            output_ocr_text="true",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_OUTPUT_OCR_TEXT.value)

    def test_validate_deidentify_file_request_invalid_masking_method(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            masking_method="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_MASKING_METHOD.value)

    def test_validate_deidentify_file_request_invalid_pixel_density(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            pixel_density="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_PIXEL_DENSITY.value)

    def test_validate_deidentify_file_request_invalid_max_resolution(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            max_resolution="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_MAXIMUM_RESOLUTION.value)

    def test_validate_deidentify_file_request_invalid_output_processed_audio(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            output_processed_audio="true",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_OUTPUT_PROCESSED_AUDIO.value)

    def test_validate_deidentify_file_request_invalid_output_transcription(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            output_transcription="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_OUTPUT_TRANSCRIPTION.value)

    def test_validate_deidentify_file_request_invalid_wait_time(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time="invalid",
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_WAIT_TIME.value)

    def test_validate_detokenize_request_valid(self):
        request = DetokenizeRequest(
            data=[{"token": "token123", "redaction": RedactionType.PLAIN_TEXT}],
            continue_on_error=False
        )
        validate_detokenize_request(self.logger, request)

    def test_validate_detokenize_request_empty_data(self):
        request = DetokenizeRequest(data=[], continue_on_error=False)
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TOKENS_LIST_VALUE.value)

    def test_validate_detokenize_request_invalid_token_type(self):
        request = DetokenizeRequest(data=[{"token": 123}], continue_on_error=False)
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_TYPE.value.format("DETOKENIZE"))

    def test_validate_detokenize_request_missing_token_key(self):
        request = DetokenizeRequest(data=[{"not_token": "value"}], continue_on_error=False)
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKENS_LIST_VALUE.value.format(str(type(request.data))))

    def test_validate_detokenize_request_invalid_continue_on_error_type(self):
        request = DetokenizeRequest(data=[{"token": "token123"}], continue_on_error="invalid")
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_CONTINUE_ON_ERROR_TYPE.value)

    def test_validate_detokenize_request_invalid_redaction_type(self):
        request = DetokenizeRequest(data=[{"token": "token123", "redaction_type": "invalid"}], continue_on_error=False)
        with self.assertRaises(SkyflowError) as context:
            validate_detokenize_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_REDACTION_TYPE.value.format(str(type("invalid"))))

    def test_validate_detokenize_request_deprecated_redaction_key_emits_warn(self):
        from unittest.mock import patch
        request = DetokenizeRequest(data=[{"token": "token123", "redaction": RedactionType.PLAIN_TEXT}], continue_on_error=False)
        with patch('skyflow.utils.validations._validations.log_warn') as mock_warn:
            validate_detokenize_request(self.logger, request)
        mock_warn.assert_called_once()
        self.assertIn("redaction_type", mock_warn.call_args[0][0])

    def test_validate_detokenize_request_both_keys_prioritizes_redaction_type_and_warns(self):
        from unittest.mock import patch
        request = DetokenizeRequest(
            data=[{"token": "token123", "redaction": RedactionType.PLAIN_TEXT, "redaction_type": RedactionType.MASKED}],
            continue_on_error=False
        )
        with patch('skyflow.utils.validations._validations.log_warn') as mock_warn:
            validate_detokenize_request(self.logger, request)
        mock_warn.assert_called_once()

    def test_validate_detokenize_request_redaction_type_only_no_warn(self):
        from unittest.mock import patch
        request = DetokenizeRequest(data=[{"token": "token123", "redaction_type": RedactionType.PLAIN_TEXT}], continue_on_error=False)
        with patch('skyflow.utils.validations._validations.log_warn') as mock_warn:
            validate_detokenize_request(self.logger, request)
        mock_warn.assert_not_called()


    def test_validate_deidentify_file_request_wait_time_negative(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=-1,
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.WAIT_TIME_GREATER_THEN_64.value)

    def test_validate_deidentify_file_request_wait_time_greater_than_64(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=65,
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.WAIT_TIME_GREATER_THEN_64.value)

    def test_validate_deidentify_file_request_wait_time_valid_boundary_lower(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=0,
            entities=[DetectEntities.SSN]
        )
        validate_deidentify_file_request(self.logger, request)

    def test_validate_deidentify_file_request_wait_time_valid_boundary_upper(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=64,
            entities=[DetectEntities.SSN]
        )
        # Should not raise an error
        validate_deidentify_file_request(self.logger, request)

    def test_validate_deidentify_file_request_wait_time_valid_float(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=32.5,
            entities=[DetectEntities.SSN]
        )
        # Should not raise an error
        validate_deidentify_file_request(self.logger, request)

    def test_validate_deidentify_file_request_wait_time_float_out_of_range(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(
            file=file_input,
            wait_time=64.1,
            entities=[DetectEntities.SSN]
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.WAIT_TIME_GREATER_THEN_64.value)
    def test_validate_credentials_with_valid_token_uri(self):
        credentials = {
            "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
            "token_uri": "https://valid-url.com"
        }
        # Should not raise
        validate_credentials(self.logger, credentials)

    def test_validate_credentials_with_invalid_token_uri_type(self):
        credentials = {
            "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
            "token_uri": 12345  # Not a string
        }
        with self.assertRaises(SkyflowError) as context:
            validate_credentials(self.logger, credentials)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_validate_credentials_with_invalid_token_uri_url(self):
        credentials = {
            "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
            "token_uri": "not_a_url"
        }
        with self.assertRaises(SkyflowError) as context:
            validate_credentials(self.logger, credentials)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_validate_update_vault_config_with_valid_token_uri(self):
        from skyflow.utils.enums import Env
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
                "token_uri": "https://valid-url.com"
            },
            "env": Env.DEV
        }
        # Should not raise
        self.assertTrue(validate_update_vault_config(self.logger, config))

    def test_validate_update_vault_config_with_invalid_token_uri_type(self):
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
                "token_uri": 12345
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_vault_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    def test_validate_update_vault_config_with_invalid_token_uri_url(self):
        config = {
            "vault_id": "vault123",
            "cluster_id": "cluster123",
            "credentials": {
                "api_key": "sky-abc12-1234567890abcdef1234567890abcdef",
                "token_uri": "not_a_url"
            }
        }
        with self.assertRaises(SkyflowError) as context:
            validate_update_vault_config(self.logger, config)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TOKEN_URI.value)

    # --- validate_file_from_request ---

    def test_validate_file_from_request_none_input(self):
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_INPUT.value)

    def test_validate_file_from_request_file_without_name_attr(self):
        file_obj = MagicMock(spec=[])  # no attributes at all
        file_input = MagicMock()
        file_input.file = file_obj
        file_input.file_path = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_TYPE.value)

    def test_validate_file_from_request_file_with_empty_name(self):
        file_obj = MagicMock()
        file_obj.name = "   "  # whitespace-only name
        file_input = MagicMock()
        file_input.file = file_obj
        file_input.file_path = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_TYPE.value)

    def test_validate_file_from_request_extension_only_name(self):
        file_obj = MagicMock()
        # A trailing-slash path gives os.path.basename() == "", so splitext returns ("", "")
        file_obj.name = "/some/directory/"
        file_input = MagicMock()
        file_input.file = file_obj
        file_input.file_path = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_NAME.value)

    def test_validate_file_from_request_empty_string_file_path(self):
        file_input = MagicMock()
        file_input.file = None
        file_input.file_path = ""  # empty string — has_file_path=True, so goes to elif branch
        with self.assertRaises(SkyflowError) as context:
            validate_file_from_request(file_input)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_DEIDENTIFY_FILE_PATH.value)

    # --- validate_deidentify_file_request bleep sub-fields ---

    def test_validate_deidentify_file_request_invalid_bleep_type(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(file=file_input, bleep="not_a_bleep")
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BLEEP_TYPE.value)

    def test_validate_deidentify_file_request_invalid_bleep_gain(self):
        file_input = FileInput(file_path=self.temp_file_path)
        bleep = Bleep(gain="loud")
        request = DeidentifyFileRequest(file=file_input, bleep=bleep)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BLEEP_GAIN.value)

    def test_validate_deidentify_file_request_invalid_bleep_frequency(self):
        file_input = FileInput(file_path=self.temp_file_path)
        bleep = Bleep(frequency="high")
        request = DeidentifyFileRequest(file=file_input, bleep=bleep)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BLEEP_FREQUENCY.value)

    def test_validate_deidentify_file_request_invalid_bleep_start_padding(self):
        file_input = FileInput(file_path=self.temp_file_path)
        bleep = Bleep(start_padding="early")
        request = DeidentifyFileRequest(file=file_input, bleep=bleep)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BLEEP_START_PADDING.value)

    def test_validate_deidentify_file_request_invalid_bleep_stop_padding(self):
        file_input = FileInput(file_path=self.temp_file_path)
        bleep = Bleep(stop_padding="late")
        request = DeidentifyFileRequest(file=file_input, bleep=bleep)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BLEEP_STOP_PADDING.value)

    # --- validate_deidentify_file_request output_directory ---

    def test_validate_deidentify_file_request_invalid_output_directory_type(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(file=file_input, output_directory=123)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_OUTPUT_DIRECTORY_VALUE.value)

    def test_validate_deidentify_file_request_output_directory_not_found(self):
        file_input = FileInput(file_path=self.temp_file_path)
        nonexistent = "/tmp/skyflow_nonexistent_dir_12345"
        request = DeidentifyFileRequest(file=file_input, output_directory=nonexistent)
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_file_request(self.logger, request)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.OUTPUT_DIRECTORY_NOT_FOUND.value.format(nonexistent)
        )

    def test_validate_deidentify_file_request_valid_output_directory(self):
        file_input = FileInput(file_path=self.temp_file_path)
        request = DeidentifyFileRequest(file=file_input, output_directory=self.temp_dir_path)
        validate_deidentify_file_request(self.logger, request)

    # --- validate_file_upload_request ---

    def test_validate_file_upload_request_none(self):
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, None)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TABLE_VALUE.value)

    def test_validate_file_upload_request_none_table(self):
        request = MagicMock()
        request.table = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TABLE_VALUE.value)

    def test_validate_file_upload_request_empty_table(self):
        request = MagicMock()
        request.table = "   "
        request.column_name = "file_col"
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.EMPTY_TABLE_VALUE.value)

    def test_validate_file_upload_request_none_column_name(self):
        request = MagicMock()
        request.table = "test_table"
        request.skyflow_id = None
        request.column_name = None
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.INVALID_FILE_COLUMN_NAME.value.format(type(None))
        )

    def test_validate_file_upload_request_empty_column_name(self):
        request = MagicMock()
        request.table = "test_table"
        request.skyflow_id = None
        request.column_name = ""
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.INVALID_FILE_COLUMN_NAME.value.format(type(""))
        )

    def test_validate_file_upload_request_empty_skyflow_id(self):
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            skyflow_id="   ",
            file_path=self.temp_file_path
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(
            context.exception.message,
            SkyflowMessages.Error.EMPTY_SKYFLOW_ID.value.format("FILE_UPLOAD")
        )

    def test_validate_file_upload_request_invalid_file_object_seek(self):
        file_obj = MagicMock()
        file_obj.seek.side_effect = OSError("seek failed")
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            file_object=file_obj
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_OBJECT.value)

    def test_validate_file_upload_request_valid_file_path(self):
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            file_path=self.temp_file_path
        )
        validate_file_upload_request(self.logger, request)

    def test_validate_file_upload_request_invalid_file_path(self):
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            file_path="/nonexistent/path/file.txt"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_PATH.value)

    def test_validate_file_upload_request_valid_base64(self):
        import base64
        encoded = base64.b64encode(b"file content").decode("utf-8")
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            base64=encoded,
            file_name="sample.txt"
        )
        validate_file_upload_request(self.logger, request)

    def test_validate_file_upload_request_base64_without_file_name(self):
        import base64
        encoded = base64.b64encode(b"file content").decode("utf-8")
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            base64=encoded
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_FILE_NAME.value)

    def test_validate_file_upload_request_invalid_base64_string(self):
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col",
            base64="not-valid-base64!!!",
            file_name="sample.txt"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_BASE64_STRING.value)

    def test_validate_file_upload_request_valid_file_object(self):
        with open(self.temp_file_path, "rb") as f:
            request = FileUploadRequest(
                table="test_table",
                column_name="file_col",
                file_object=f
            )
            validate_file_upload_request(self.logger, request)

    def test_validate_file_upload_request_missing_file_source(self):
        request = FileUploadRequest(
            table="test_table",
            column_name="file_col"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_file_upload_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.MISSING_FILE_SOURCE.value)

    # --- validate_deidentify_text_request transformations ---

    def test_validate_deidentify_text_request_invalid_transformations(self):
        request = DeidentifyTextRequest(
            text="test text",
            transformations="invalid_type"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_deidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message, SkyflowMessages.Error.INVALID_TRANSFORMATIONS.value)

    # --- validate_reidentify_text_request masked_entities ---

    def test_validate_reidentify_text_request_invalid_masked_entities(self):
        request = ReidentifyTextRequest(
            text="test text",
            masked_entities="invalid_type"
        )
        with self.assertRaises(SkyflowError) as context:
            validate_reidentify_text_request(self.logger, request)
        self.assertEqual(context.exception.message,
            SkyflowMessages.Error.INVALID_MASKED_ENTITIES_IN_REIDENTIFY.value)