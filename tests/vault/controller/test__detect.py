import unittest
from unittest.mock import Mock, patch, MagicMock
import base64
import os
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.vault.controller import Detect
from skyflow.vault.detect import DeidentifyTextRequest, ReidentifyTextRequest, \
    TokenFormat, DateTransformation, Transformations, DeidentifyFileRequest, GetDetectRunRequest, DeidentifyFileResponse
from skyflow.utils.enums import DetectEntities, TokenType

VAULT_ID = "test_vault_id"

class TestDetect(unittest.TestCase):
    def setUp(self):
        # Mock vault client
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = VAULT_ID
        self.vault_client.get_logger.return_value = Mock()

        # Create a Detect instance with the mock client
        self.detect = Detect(self.vault_client)

    @patch("skyflow.vault.controller._detect.validate_deidentify_text_request")
    @patch("skyflow.vault.controller._detect.parse_deidentify_text_response")
    def test_deidentify_text_success(self, mock_parse_response, mock_validate):
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = {
            'text': '[TOKEN_1] lives in [TOKEN_2]',
            'entities': [
                {
                    'token': 'Token1',
                    'value': 'John',
                    'text_index': {'start': 0, 'end': 4},
                    'processed_index': {'start': 0, 'end': 8},
                    'entity': 'NAME',
                    'scores': {'confidence': 0.9}
                }
            ],
            'word_count': 4,
            'char_count': 20
        }

        # Create request
        request = DeidentifyTextRequest(
            text="John lives in NYC",
            entities=[DetectEntities.NAME],
            token_format=TokenFormat(default=TokenType.ENTITY_ONLY)
        )

        # Mock detect API
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.deidentify_string.return_value = mock_api_response

        # Call deidentify_text
        response = self.detect.deidentify_text(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)
        detect_api.deidentify_string.assert_called_once()

    @patch("skyflow.vault.controller._detect.validate_reidentify_text_request")
    @patch("skyflow.vault.controller._detect.parse_reidentify_text_response")
    def test_reidentify_text_success(self, mock_parse_response, mock_validate):
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = {
            'text': 'John lives in NYC'
        }

        # Create request
        request = ReidentifyTextRequest(
            text="Token1 lives in Token2",
            redacted_entities=[DetectEntities.NAME]
        )

        # Mock detect API
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.reidentify_string.return_value = mock_api_response

        # Call reidentify_text
        response = self.detect.reidentify_text(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)
        detect_api.reidentify_string.assert_called_once()

    @patch("skyflow.vault.controller._detect.validate_deidentify_text_request")
    def test_deidentify_text_handles_generic_error(self, mock_validate):
        request = DeidentifyTextRequest(
            text="John lives in NYC",
            entities=[DetectEntities.NAME]
        )
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.deidentify_string.side_effect = Exception("Generic Error")

        with self.assertRaises(Exception):
            self.detect.deidentify_text(request)

        detect_api.deidentify_string.assert_called_once()

    @patch("skyflow.vault.controller._detect.validate_reidentify_text_request")
    def test_reidentify_text_handles_generic_error(self, mock_validate):
        request = ReidentifyTextRequest(
            text="Token1 lives in Token2",
            redacted_entities=[DetectEntities.NAME]
        )
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.reidentify_string.side_effect = Exception("Generic Error")

        with self.assertRaises(Exception):
            self.detect.reidentify_text(request)

        detect_api.reidentify_string.assert_called_once()

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    @patch("skyflow.vault.controller._detect.os.path.basename")
    @patch("skyflow.vault.controller._detect.open", create=True)
    def test_deidentify_file_txt_success(self, mock_open, mock_basename, mock_base64, mock_validate):
        file_content = b"test content"
        file_obj = Mock()
        file_obj.read.return_value = file_content
        file_obj.name = "/tmp/test.txt"
        mock_basename.return_value = "test.txt"
        mock_base64.b64encode.return_value = b"dGVzdCBjb250ZW50"
        req = DeidentifyFileRequest(file=file_obj)
        req.entities = []
        req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = "/tmp"
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.deidentify_text = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        api_response = Mock()
        api_response.data = Mock(run_id="runid123")
        files_api.deidentify_text.return_value = api_response

        processed_response = Mock()
        processed_response.status = "SUCCESS"
        processed_response.output = []
        processed_response.word_character_count = Mock(word_count=1, character_count=1)
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                          return_value=processed_response) as mock_poll, \
                patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                             return_value=DeidentifyFileResponse(file="dGVzdCBjb250ZW50", type="txt", extension="txt",
                                                                 word_count=1, char_count=1, size_in_kb=1,
                                                                 duration_in_seconds=None, page_count=None,
                                                                 slide_count=None, entities=[], run_id="runid123",
                                                                 status="SUCCESS", errors=[])) as mock_parse:
            result = self.detect.deidentify_file(req)
            mock_validate.assert_called_once()
            files_api.deidentify_text.assert_called_once()
            mock_poll.assert_called_once()
            mock_parse.assert_called_once()
            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    def test_deidentify_file_audio_success(self, mock_base64, mock_validate):
        file_content = b"audio bytes"
        file_obj = Mock()
        file_obj.read.return_value = file_content
        file_obj.name = "audio.mp3"
        mock_base64.b64encode.return_value = b"YXVkaW8gYnl0ZXM="
        req = DeidentifyFileRequest(file=file_obj)
        req.entities = []
        req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = None
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.deidentify_audio = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        api_response = Mock()
        api_response.data = Mock(run_id="runid456")
        files_api.deidentify_audio.return_value = api_response

        processed_response = Mock()
        processed_response.status = "SUCCESS"
        processed_response.output = []
        processed_response.word_character_count = Mock(word_count=1, character_count=1)
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                          return_value=processed_response) as mock_poll, \
                patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                             return_value=DeidentifyFileResponse(file="YXVkaW8gYnl0ZXM=", type="mp3", extension="mp3",
                                                                 word_count=1, char_count=1, size_in_kb=1,
                                                                 duration_in_seconds=1, page_count=None,
                                                                 slide_count=None, entities=[], run_id="runid456",
                                                                 status="SUCCESS", errors=[])) as mock_parse:
            result = self.detect.deidentify_file(req)
            mock_validate.assert_called_once()
            files_api.deidentify_audio.assert_called_once()
            mock_poll.assert_called_once()
            mock_parse.assert_called_once()
            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    def test_deidentify_file_exception(self, mock_validate):
        req = DeidentifyFileRequest(file=Mock())
        req.entities = []
        req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = None
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.deidentify_text.side_effect = Exception("API Error")
        self.vault_client.get_detect_file_api.return_value = files_api
        with self.assertRaises(Exception):
            self.detect.deidentify_file(req)

    @patch("skyflow.vault.controller._detect.validate_get_detect_run_request")
    def test_get_detect_run_success(self, mock_validate):
        req = GetDetectRunRequest(run_id="runid789")
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.get_run = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        response = Mock()
        response.status = "SUCCESS"
        response.output = []
        response.word_character_count = Mock(word_count=1, character_count=1)
        files_api.get_run.return_value = response
        with patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                          return_value=DeidentifyFileResponse(file="file", type="txt", extension="txt", word_count=1,
                                                              char_count=1, size_in_kb=1, duration_in_seconds=None,
                                                              page_count=None, slide_count=None, entities=[],
                                                              run_id="runid789", status="SUCCESS",
                                                              errors=[])) as mock_parse:
            result = self.detect.get_detect_run(req)
            mock_validate.assert_called_once()
            files_api.get_run.assert_called_once()
            mock_parse.assert_called_once()
            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")

    @patch("skyflow.vault.controller._detect.validate_get_detect_run_request")
    def test_get_detect_run_exception(self, mock_validate):
        req = GetDetectRunRequest(run_id="runid789")
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.get_run.side_effect = Exception("API Error")
        self.vault_client.get_detect_file_api.return_value = files_api
        with self.assertRaises(Exception):
            self.detect.get_detect_run(req)

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    @patch("skyflow.vault.controller._detect.os.path.basename")
    @patch("skyflow.vault.controller._detect.open", create=True)
    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_deidentify_file_all_branches(self, mock_sleep, mock_open, mock_basename, mock_base64, mock_validate):
        # Helper to run a branch
        def run_branch(file_name, file_extension, api_call_attr, req_file_class):
            file_content = b"test content"
            file_obj = Mock()
            file_obj.read.return_value = file_content
            file_obj.name = file_name
            mock_basename.return_value = os.path.basename(file_name)
            mock_base64.b64encode.return_value = b"dGVzdCBjb250ZW50"
            req = DeidentifyFileRequest(file=file_obj)
            req.entities = []
            req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
            req.allow_regex_list = []
            req.restrict_regex_list = []
            req.transformations = None
            req.output_directory = "/tmp"
            files_api = Mock()
            files_api.with_raw_response = files_api
            setattr(files_api, api_call_attr, Mock())
            self.vault_client.get_detect_file_api.return_value = files_api
            api_response = Mock()
            api_response.data = Mock(run_id="runid123")
            getattr(files_api, api_call_attr).return_value = api_response

            # Patch get_run for polling
            poll_response = Mock()
            poll_response.status = "SUCCESS"
            poll_response.output = [
                {"processedFile": "dGVzdCBjb250ZW50", "processedFileType": file_extension,
                 "processedFileExtension": file_extension}
            ]
            poll_response.word_character_count = Mock(word_count=1, character_count=1)
            poll_response.size = 1
            poll_response.duration = 1
            poll_response.pages = 1
            poll_response.slides = 1
            poll_response.message = ""
            poll_response.run_id = "runid123"
            files_api.get_run.return_value = poll_response

            # Actually run the method (no patching of __poll_for_processed_file or __parse_deidentify_file_response)
            result = self.detect.deidentify_file(req)
            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.file, "dGVzdCBjb250ZW50")
            self.assertEqual(result.type, file_extension)
            self.assertEqual(result.extension, file_extension)

        # Test all branches
        run_branch("test.pdf", "pdf", "deidentify_pdf", "DeidentifyPdfRequestFile")
        run_branch("test.jpg", "jpg", "deidentify_image", "DeidentifyImageRequestFile")
        run_branch("test.pptx", "pptx", "deidentify_presentation", "DeidentifyPresentationRequestFile")
        run_branch("test.csv", "csv", "deidentify_spreadsheet", "DeidentifySpreadsheetRequestFile")
        run_branch("test.docx", "docx", "deidentify_document", "DeidentifyDocumentRequestFile")
        run_branch("test.json", "json", "deidentify_structured_text", "DeidentifyStructuredTextRequestFile")
        run_branch("test.xml", "xml", "deidentify_structured_text", "DeidentifyStructuredTextRequestFile")
        # Test else branch (unknown extension)
        run_branch("test.unknown", "unknown", "deidentify_file", "DeidentifyFileRequestFile")

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    def test_deidentify_file_exception(self, mock_base64, mock_validate):
        file_obj = Mock()
        file_obj.read.side_effect = Exception("Read error")
        file_obj.name = "test.txt"
        req = DeidentifyFileRequest(file=file_obj)
        req.entities = []
        req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = None
        with self.assertRaises(Exception):
            self.detect.deidentify_file(req)

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_success(self, mock_sleep):
        files_api = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        # First call returns IN_PROGRESS, second call returns SUCCESS
        in_progress = Mock()
        in_progress.status = "IN_PROGRESS"
        in_progress.message = ""
        success = Mock()
        success.status = "SUCCESS"
        files_api.get_run.side_effect = [in_progress, success]
        result = self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=2)
        self.assertEqual(result.status, "SUCCESS")

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_failed(self, mock_sleep):
        files_api = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        failed = Mock()
        failed.status = "FAILED"
        failed.message = "fail"
        files_api.get_run.return_value = failed
        with self.assertRaises(SkyflowError):
            self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=1)

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_unknown(self, mock_sleep):
        files_api = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        unknown = Mock()
        unknown.status = "UNKNOWN"
        unknown.message = "fail"
        files_api.get_run.return_value = unknown
        with self.assertRaises(SkyflowError):
            self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=1)

    def test_parse_deidentify_file_response_dict_and_obj(self):
        # Dict input
        data = {
            "output": [
                {"processedFile": "abc", "processedFileType": "pdf", "processedFileExtension": "pdf"},
                {"processedFile": "def", "processedFileType": "entities", "processedFileExtension": "json"}
            ],
            "word_character_count": {"word_count": 5, "character_count": 10},
            "size": 1,
            "duration": 2,
            "pages": 3,
            "slides": 4,
            "run_id": "runid",
            "status": "SUCCESS"
        }
        result = self.detect._Detect__parse_deidentify_file_response(data, "runid", "SUCCESS")
        self.assertIsInstance(result, DeidentifyFileResponse)

        # Object input
        class DummyWordChar:
            word_count = 7
            character_count = 14

        class DummyData:
            output = [
                type("O", (),
                     {"processed_file": "abc", "processed_file_type": "pdf", "processed_file_extension": "pdf"})(),
                type("O", (),
                     {"processed_file": "def", "processed_file_type": "entities", "processed_file_extension": "json"})()
            ]
            word_character_count = DummyWordChar()
            size = 1
            duration = 2
            pages = 3
            slides = 4
            run_id = "runid"
            status = "SUCCESS"

        obj_data = DummyData()
        result = self.detect._Detect__parse_deidentify_file_response(obj_data, "runid", "SUCCESS")
        self.assertIsInstance(result, DeidentifyFileResponse)
    def test_get_token_format_missing_attribute(self):
        """Test __get_token_format when token_format attribute is missing"""
        class DummyRequest:
            pass
        request = DummyRequest()
        result = self.detect._Detect__get_token_format(request)
        self.assertIsNone(result)

    def test_get_transformations_missing_shift_dates(self):
        """Test __get_transformations when shift_dates is None"""
        class DummyTransformations:
            shift_dates = None
        class DummyRequest:
            transformations = DummyTransformations()
        request = DummyRequest()
        result = self.detect._Detect__get_transformations(request)
        self.assertIsNone(result)

    @patch("skyflow.vault.controller._detect.validate_get_detect_run_request")
    def test_get_detect_run_in_progress_status(self, mock_validate):
        """Test get_detect_run when status is IN_PROGRESS"""
        # Setup
        run_id = "test_run_id"
        req = GetDetectRunRequest(run_id=run_id)

        # Mock API response
        files_api = Mock()
        files_api.with_raw_response = files_api
        mock_response = Mock()
        mock_response.data = Mock()
        mock_response.data.status = 'IN_PROGRESS'
        files_api.get_run.return_value = mock_response

        self.vault_client.get_detect_file_api.return_value = files_api

        # Execute
        with patch.object(self.detect, "_Detect__parse_deidentify_file_response") as mock_parse:
            result = self.detect.get_detect_run(req)

            # Verify IN_PROGRESS handling
            mock_parse.assert_called_once()
            args = mock_parse.call_args[0][0]
            self.assertIsInstance(args, DeidentifyFileResponse)
            self.assertEqual(args.status, 'IN_PROGRESS')
            self.assertEqual(args.run_id, run_id)
