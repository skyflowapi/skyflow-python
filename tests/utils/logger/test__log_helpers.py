import unittest
from unittest.mock import Mock, patch

from skyflow import LogLevel
from skyflow.utils.logger import log_info, log_error


class TestLoggingFunctions(unittest.TestCase):

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_info_with_logger(self, MockLogger):
        mock_logger = MockLogger()
        message = "Info message"
        interface = "InterfaceA"

        log_info(message, mock_logger)

        mock_logger.info.assert_called_once_with(f"{message}")

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_info_without_logger(self, MockLogger):
        try:
            log_info("Message", None)
        except AttributeError:
            self.fail("log_info raised AttributeError unexpectedly!")

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_error_with_all_fields(self, MockLogger):
        mock_logger = MockLogger()
        message = "Error message"
        http_code = 404
        grpc_code = 5
        http_status = "Not Found"
        request_id = "12345"
        details = {"info": "Detailed error information"}

        log_error(message, http_code, request_id, grpc_code, http_status, details, mock_logger)

        expected_log_data = {
            'http_code': http_code,
            'message': message,
            'grpc_code': grpc_code,
            'http_status': http_status,
            'request_id': request_id,
            'details': details
        }

        mock_logger.error.assert_called_once_with(expected_log_data)

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_error_with_minimal_fields(self, MockLogger):
        mock_logger = MockLogger()
        message = "Minimal error"
        http_code = 400

        log_error(message, http_code, logger=mock_logger)

        expected_log_data = {
            'http_code': http_code,
            'message': message
        }

        mock_logger.error.assert_called_once_with(expected_log_data)

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_error_creates_logger_if_none(self, MockLogger):
        message = "Auto-created logger error"
        http_code = 500

        log_error(message, http_code)

        MockLogger.assert_called_once_with(LogLevel.ERROR)

    @patch('skyflow.utils.logger._log_helpers.Logger')
    def test_log_error_handles_missing_optional_fields(self, MockLogger):
        mock_logger = MockLogger()
        message = "Test missing optional fields"
        http_code = 503

        log_error(message, http_code, logger=mock_logger)

        expected_log_data = {
            'http_code': http_code,
            'message': message
        }
        mock_logger.error.assert_called_once_with(expected_log_data)
