import unittest
from unittest.mock import Mock, patch
from skyflow.error import SkyflowError
from skyflow.vault.controller import Detect
from skyflow.vault.detect import DeidentifyTextRequest, ReidentifyTextRequest, \
    TokenFormat, DateTransformation, Transformations
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


# if __name__ == '__main__':
#     unittest.main()
