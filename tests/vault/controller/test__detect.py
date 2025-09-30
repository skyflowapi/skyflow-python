import unittest
from unittest.mock import Mock, patch, MagicMock
import base64
import os
from skyflow.error import SkyflowError
from skyflow.utils import SkyflowMessages
from skyflow.vault.controller import Detect
from skyflow.vault.detect import DeidentifyTextRequest, ReidentifyTextRequest, \
    TokenFormat, DateTransformation, Transformations, DeidentifyFileRequest, GetDetectRunRequest, \
    DeidentifyFileResponse, FileInput
from skyflow.utils.enums import DetectEntities, TokenType
import io

from skyflow.vault.detect._file import File

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
            'wordCount': 4,
            'charCount': 20
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
        req = DeidentifyFileRequest(file=FileInput(file=file_obj))
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
        processed_response.wordCharacterCount = Mock(wordCount=1, characterCount=1)
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                          return_value=processed_response) as mock_poll, \
                patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                             return_value=DeidentifyFileResponse(file_base64="dGVzdCBjb250ZW50",
                                                                 file=io.BytesIO(b"test content"), type="txt",
                                                                 extension="txt",
                                                                 word_count=1, char_count=1, size_in_kb=1,
                                                                 duration_in_seconds=None, page_count=None,
                                                                 slide_count=None, entities=[], run_id="runid123",
                                                                 status="SUCCESS")) as mock_parse:
            result = self.detect.deidentify_file(req)

            mock_validate.assert_called_once()
            files_api.deidentify_text.assert_called_once()
            mock_poll.assert_called_once()
            mock_parse.assert_called_once()

            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.run_id, "runid123")
            self.assertEqual(result.file_base64, "dGVzdCBjb250ZW50")
            self.assertEqual(result.type, "txt")
            self.assertEqual(result.extension, "txt")

            self.assertIsInstance(result.file, File)
            result.file.seek(0)
            self.assertEqual(result.file.read(), b"test content")
            self.assertEqual(result.word_count, 1)
            self.assertEqual(result.char_count, 1)
            self.assertEqual(result.size_in_kb, 1)
            self.assertIsNone(result.duration_in_seconds)
            self.assertIsNone(result.page_count)
            self.assertIsNone(result.slide_count)
            self.assertEqual(result.entities, [])

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    def test_deidentify_file_audio_success(self, mock_base64, mock_validate):
        file_content = b"audio bytes"
        file_obj = Mock()
        file_obj.read.return_value = file_content
        file_obj.name = "audio.mp3"
        mock_base64.b64encode.return_value = b"YXVkaW8gYnl0ZXM="
        req = DeidentifyFileRequest(file=FileInput(file=file_obj))
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
        processed_response.wordCharacterCount = Mock(wordCount=1, characterCount=1)
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                          return_value=processed_response) as mock_poll, \
                patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                             return_value=DeidentifyFileResponse(file_base64="YXVkaW8gYnl0ZXM=",
                                                                 file=io.BytesIO(b"audio bytes"), type="mp3",
                                                                 extension="mp3",
                                                                 word_count=1, char_count=1, size_in_kb=1,
                                                                 duration_in_seconds=1, page_count=None,
                                                                 slide_count=None, entities=[], run_id="runid456",
                                                                 status="SUCCESS")) as mock_parse:
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
        response.wordCharacterCount = Mock(wordCount=1, characterCount=1)
        files_api.get_run.return_value = response
        with patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                          return_value=DeidentifyFileResponse(file="file", type="txt", extension="txt", word_count=1,
                                                              char_count=1, size_in_kb=1, duration_in_seconds=None,
                                                              page_count=None, slide_count=None, entities=[],
                                                              run_id="runid789", status="SUCCESS")) as mock_parse:
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
    @patch.object(Detect, "_Detect__poll_for_processed_file")
    def test_deidentify_file_all_branches(self, mock_poll, mock_open, mock_basename, mock_base64, mock_validate):
        # Common mocks
        file_content = b"test content"
        mock_base64.b64encode.return_value = b"dGVzdCBjb250ZW50"
        mock_base64.b64decode.return_value = file_content

        # Prepare a generic processed_response for all branches
        processed_response = Mock()
        processed_response.status = "SUCCESS"
        processed_response.output = [
            {"processedFile": "dGVzdCBjb250ZW50", "processedFileType": "pdf", "processedFileExtension": "pdf"}
        ]
        processed_response.wordCharacterCount = Mock(wordCount=1, characterCount=1)
        processed_response.size = 1
        processed_response.duration = 1
        processed_response.pages = 1
        processed_response.slides = 1
        processed_response.message = ""
        processed_response.run_id = "runid123"
        processed_response.wordCharacterCount = {"wordCount": 1, "characterCount": 1}
        mock_poll.return_value = processed_response

        # Test configuration for different file types
        test_cases = [
            ("test.pdf", "pdf", "deidentify_pdf"),
            ("test.jpg", "jpg", "deidentify_image"),
            ("test.pptx", "pptx", "deidentify_presentation"),
            ("test.csv", "csv", "deidentify_spreadsheet"),
            ("test.docx", "docx", "deidentify_document"),
            ("test.json", "json", "deidentify_structured_text"),
            ("test.xml", "xml", "deidentify_structured_text"),
            ("test.unknown", "unknown", "deidentify_file")
        ]

        for file_name, extension, api_method in test_cases:
            with self.subTest(file_type=extension):
                # Setup file mock
                file_obj = Mock()
                file_obj.read.return_value = file_content
                file_obj.name = file_name
                mock_basename.return_value = file_name

                # Setup request with FileInput
                req = DeidentifyFileRequest(file=FileInput(file=file_obj))
                req.entities = []
                req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
                req.allow_regex_list = []
                req.restrict_regex_list = []
                req.transformations = None
                req.output_directory = "/tmp"

                # Setup API mock
                files_api = Mock()
                files_api.with_raw_response = files_api
                api_method_mock = Mock()
                setattr(files_api, api_method, api_method_mock)
                self.vault_client.get_detect_file_api.return_value = files_api

                # Setup API response
                api_response = Mock()
                api_response.data = Mock(run_id="runid123")
                api_method_mock.return_value = api_response

                # Actually run the method
                result = self.detect.deidentify_file(req)

                # Verify the result
                self.assertIsInstance(result, DeidentifyFileResponse)
                self.assertEqual(result.status, "SUCCESS")
                self.assertEqual(result.run_id, "runid123")
                self.assertEqual(result.file_base64, "dGVzdCBjb250ZW50")
                self.assertIsInstance(result.file, File)
                result.file.seek(0)  # Reset file pointer before reading
                self.assertEqual(result.file.read(), b"test content")
                self.assertEqual(result.type, "pdf")
                self.assertEqual(result.extension, "pdf")
                self.assertEqual(result.size_in_kb, 1)
                self.assertEqual(result.duration_in_seconds, 1)
                self.assertEqual(result.page_count, 1)
                self.assertEqual(result.slide_count, 1)
                self.assertEqual(result.word_count, 1)
                self.assertEqual(result.char_count, 1)

                # Verify API was called
                api_method_mock.assert_called_once()
                mock_poll.assert_called_with("runid123", None)

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    def test_deidentify_file_exception(self, mock_base64, mock_validate):
        file_obj = Mock()
        file_obj.read.side_effect = Exception("Read error")
        file_obj.name = "test.txt"
        req = DeidentifyFileRequest(file=FileInput(file=file_obj))
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
        files_api.with_raw_response = files_api
        self.vault_client.get_detect_file_api.return_value = files_api

        call_count = {"count": 0}

        def get_run_side_effect(*args, **kwargs):
            if call_count["count"] < 1:
                call_count["count"] += 1
                in_progress = Mock()
                in_progress.status = "IN_PROGRESS"
                in_progress.message = ""
                return Mock(data=in_progress)
            else:
                success = Mock()
                success.status = "SUCCESS"
                return Mock(data=success)

        files_api.get_run.side_effect = get_run_side_effect

        # Use max_wait_time > 1 to allow the loop to reach the SUCCESS status
        result = self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=2)
        self.assertEqual(result.status, "SUCCESS")

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_failed(self, mock_sleep):
        files_api = Mock()
        files_api.with_raw_response = files_api
        self.vault_client.get_detect_file_api.return_value = files_api

        # Always return FAILED on first call
        def get_run_side_effect(*args, **kwargs):
            failed = Mock()
            failed.status = "FAILED"
            failed.message = "fail"
            return Mock(data=failed)

        files_api.get_run.side_effect = get_run_side_effect

        result = self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=1)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.message, "fail")

    def test_parse_deidentify_file_response_dict_and_obj(self):
        # Dict input
        data = {
            "output": [
                {"processedFile": "YWJj", "processedFileType": "pdf", "processedFileExtension": "pdf"},  # base64 for "abc"
                {"processedFile": "ZGVm", "processedFileType": "entities", "processedFileExtension": "json"}  # base64 for "def"
            ],
            "wordCharacterCount": {"wordCount": 5, "characterCount": 10},
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
            wordCount = 7
            characterCount = 14

        class DummyData:
            output = [
                type("O", (),
                     {"processed_file": "YWJj", "processed_file_type": "pdf", "processed_file_extension": "pdf"})(),
                type("O", (),
                     {"processed_file": "ZGVm", "processed_file_type": "entities", "processed_file_extension": "json"})()
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
        self.assertEqual(result.file_base64, "YWJj")
        self.assertIsInstance(result.file, File)
        self.assertEqual(result.file.read(), b"abc")
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

    def test_get_transformations_with_shift_dates(self):

        class DummyShiftDates:
            max = 30
            min = 10
            entities = ["SSN"]

        class DummyTransformations:
            shift_dates = DummyShiftDates()

        class DummyRequest:
            transformations = DummyTransformations()

        request = DummyRequest()
        result = self.detect._Detect__get_transformations(request)

        self.assertEqual(result, {
            'shift_dates': {
                'max_days': 30,
                'min_days': 10,
                'entity_types': ["SSN"]
            }
        })

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_timeout(self, mock_sleep):
        """Test polling timeout returns IN_PROGRESS status"""
        files_api = Mock()
        files_api.with_raw_response = files_api
        self.vault_client.get_detect_file_api.return_value = files_api

        # Always return IN_PROGRESS
        def get_run_side_effect(*args, **kwargs):
            in_progress = Mock()
            in_progress.status = "IN_PROGRESS"
            return Mock(data=in_progress)

        files_api.get_run.side_effect = get_run_side_effect

        result = self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=1)
        self.assertIsInstance(result, DeidentifyFileResponse)
        self.assertEqual(result.status, "IN_PROGRESS")
        self.assertEqual(result.run_id, "runid123")

    @patch("skyflow.vault.controller._detect.time.sleep", return_value=None)
    def test_poll_for_processed_file_wait_time_calculation(self, mock_sleep):
        """Test wait time calculation in polling loop"""
        files_api = Mock()
        files_api.with_raw_response = files_api
        self.vault_client.get_detect_file_api.return_value = files_api

        calls = []

        def track_sleep(*args):
            calls.append(args[0])  # Record wait time

        mock_sleep.side_effect = track_sleep

        # Return IN_PROGRESS twice then SUCCESS
        responses = [
            Mock(data=Mock(status="IN_PROGRESS")),
            Mock(data=Mock(status="IN_PROGRESS")),
            Mock(data=Mock(status="SUCCESS"))
        ]
        files_api.get_run.side_effect = responses

        result = self.detect._Detect__poll_for_processed_file("runid123", max_wait_time=4)

        self.assertEqual(calls, [2, 2])
        self.assertEqual(result.status, "SUCCESS")

    def test_parse_deidentify_file_response_output_conversion(self):
        """Test output conversion in parse_deidentify_file_response"""

        class OutputObj:
            processed_file = "YWJjMTIz"  # base64 for "abc123"
            processed_file_type = "pdf"
            processed_file_extension = "pdf"

        data = Mock()
        data.output = [OutputObj()]
        data.size = 1
        data.wordCharacterCount = Mock(wordCount=1, characterCount=1)

        result = self.detect._Detect__parse_deidentify_file_response(data)

        # Check base64 string
        self.assertEqual(result.file_base64, "YWJjMTIz")
        # Check File object
        self.assertIsInstance(result.file, File)
        self.assertEqual(result.file.read(), b"abc123")
        # Check other attributes
        self.assertEqual(result.type, "pdf")
        self.assertEqual(result.extension, "pdf")
        # Reset file pointer and verify content again
        result.file.seek(0)
        self.assertEqual(result.file.read(), b"abc123")

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    @patch("skyflow.vault.controller._detect.os.path.basename")
    @patch("skyflow.vault.controller._detect.open", create=True)
    def test_deidentify_file_using_file_path(self, mock_open, mock_basename, mock_base64, mock_validate):
        # Setup mock file context
        mock_file = MagicMock()
        mock_file.read.return_value = b"test content from file path"
        mock_file.name = "/path/to/test.txt"
        mock_file.__enter__.return_value = mock_file  # Mock context manager
        mock_open.return_value = mock_file
        mock_basename.return_value = "test.txt"
        mock_base64.b64encode.return_value = b"dGVzdCBjb250ZW50IGZyb20gZmlsZSBwYXRo"  # base64 of "test content from file path"
        mock_base64.b64decode.return_value = b"test content from file path"
        # Create request with file_path
        req = DeidentifyFileRequest(file=FileInput(file_path="/path/to/test.txt"))
        req.entities = []
        req.token_format = Mock(default="default", entity_unique_counter=[], entity_only=[])
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = "/tmp"

        # Setup API mock
        files_api = Mock()
        files_api.with_raw_response = files_api
        files_api.deidentify_text = Mock()
        self.vault_client.get_detect_file_api.return_value = files_api
        api_response = Mock()
        api_response.data = Mock(run_id="runid123")
        files_api.deidentify_text.return_value = api_response

        # Setup processed response
        processed_response = Mock()
        processed_response.status = "SUCCESS"
        processed_response.output = [
            Mock(processedFile="dGVzdCBjb250ZW",
                 processedFileType="txt",
                 processedFileExtension="txt")
        ]
        processed_response.wordCharacterCount = Mock(wordCount=1, characterCount=1)

        # Test the method
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                         return_value=processed_response) as mock_poll, \
             patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                         return_value=DeidentifyFileResponse(
                             file_base64="dGVzdCBjb250ZW50IGZyb20gZmlsZSBwYXRo",
                             file=io.BytesIO(b"test content from file path"),
                             type="txt",
                             extension="txt",
                             word_count=1,
                             char_count=1,
                             size_in_kb=1,
                             duration_in_seconds=None,
                             page_count=None,
                             slide_count=None,
                             entities=[],
                             run_id="runid123",
                             status="SUCCESS",
                         )) as mock_parse:
            
            result = self.detect.deidentify_file(req)

            mock_file.read.assert_called_once()
            mock_validate.assert_called_once()
            files_api.deidentify_text.assert_called_once()
            mock_basename.assert_called_with("/path/to/test.txt")
            mock_poll.assert_called_once()
            mock_parse.assert_called_once()

            # Response assertions
            self.assertIsInstance(result, DeidentifyFileResponse)
            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.run_id, "runid123")
            self.assertEqual(result.file_base64, "dGVzdCBjb250ZW50IGZyb20gZmlsZSBwYXRo")
            self.assertEqual(result.type, "txt")
            self.assertEqual(result.extension, "txt")

            self.assertIsInstance(result.file, File)
            result.file.seek(0)
            self.assertEqual(result.file.read(), b"test content from file path")
            self.assertEqual(result.word_count, 1)
            self.assertEqual(result.char_count, 1)
            self.assertEqual(result.size_in_kb, 1)
            self.assertIsNone(result.duration_in_seconds)
            self.assertIsNone(result.page_count)
            self.assertIsNone(result.slide_count)
            self.assertEqual(result.entities, [])
