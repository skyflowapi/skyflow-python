import unittest
from unittest.mock import patch, Mock
import logging
from skyflow import LogLevel
from skyflow.utils.logger import Logger


class TestLogger(unittest.TestCase):

    @patch('logging.getLogger')
    def test_logger_initialization_with_default_level(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger()

        self.assertEqual(logger.current_level, LogLevel.ERROR)
        mock_logger_instance.setLevel.assert_called_once_with(logging.ERROR)

    @patch('logging.getLogger')
    def test_logger_initialization_with_custom_level(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.INFO)

        self.assertEqual(logger.current_level, LogLevel.INFO)
        mock_logger_instance.setLevel.assert_called_once_with(logging.INFO)

    @patch('logging.getLogger')
    def test_set_log_level(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger()
        logger.set_log_level(LogLevel.DEBUG)

        self.assertEqual(logger.current_level, LogLevel.DEBUG)
        mock_logger_instance.setLevel.assert_called_with(logging.DEBUG)

    @patch('logging.getLogger')
    def test_debug_logging(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.DEBUG)
        logger.debug("Debug message")

        mock_logger_instance.debug.assert_called_once_with("Debug message")

    @patch('logging.getLogger')
    def test_info_logging(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.INFO)
        logger.info("Info message")

        mock_logger_instance.info.assert_called_once_with("Info message")
        mock_logger_instance.debug.assert_not_called()

    @patch('logging.getLogger')
    def test_warn_logging(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.WARN)
        logger.warn("Warn message")

        mock_logger_instance.warning.assert_called_once_with("Warn message")
        mock_logger_instance.info.assert_not_called()
        mock_logger_instance.debug.assert_not_called()

    @patch('logging.getLogger')
    def test_error_logging(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.ERROR)
        logger.error("Error message")

        mock_logger_instance.error.assert_called_once_with("Error message")
        mock_logger_instance.warning.assert_not_called()
        mock_logger_instance.info.assert_not_called()
        mock_logger_instance.debug.assert_not_called()

    @patch('logging.getLogger')
    def test_logging_with_level_off(self, mock_get_logger):
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = Logger(LogLevel.OFF)
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warn("Warn message")
        logger.error("Error message")

        mock_logger_instance.debug.assert_not_called()
        mock_logger_instance.info.assert_not_called()
        mock_logger_instance.warning.assert_not_called()
        mock_logger_instance.error.assert_not_called()