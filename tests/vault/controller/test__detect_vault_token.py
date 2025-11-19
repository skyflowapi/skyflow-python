import unittest
from unittest.mock import Mock, patch
import io
from skyflow.vault.controller import Detect
from skyflow.vault.detect import (
    DeidentifyTextRequest, 
    DeidentifyFileRequest, 
    DeidentifyFileResponse,
    FileInput,
    TokenFormat
)
from skyflow.utils.enums import DetectEntities, TokenType
from skyflow.generated.rest import WordCharacterCount


class TestDetectVaultToken(unittest.TestCase):
    """Tests for vault token support in Detect API"""
    
    def setUp(self):
        # Mock vault client
        self.vault_client = Mock()
        self.vault_client.get_vault_id.return_value = "test_vault_id"
        self.vault_client.get_logger.return_value = Mock()
        
        # Create a Detect instance with the mock client
        self.detect = Detect(self.vault_client)

    @patch("skyflow.vault.controller._detect.validate_deidentify_text_request")
    @patch("skyflow.vault.controller._detect.parse_deidentify_text_response")
    def test_deidentify_text_with_vault_token_default(self, mock_parse_response, mock_validate):
        """Test deidentify_text with VAULT_TOKEN as default token type"""
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = {
            'text': '[SSN_VqLazzA] and [CREDIT_CARD_54lAgtk]',
            'entities': []
        }

        # Create request with VAULT_TOKEN
        request = DeidentifyTextRequest(
            text="My SSN is 123-45-6789 and my card is 4111 1111 1111 1111",
            entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
            token_format=TokenFormat(default=TokenType.VAULT_TOKEN)
        )

        # Mock detect API
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.deidentify_string.return_value = mock_api_response

        # Call deidentify_text
        response = self.detect.deidentify_text(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)
        
        # Verify the API was called with vault_token in token_type
        detect_api.deidentify_string.assert_called_once()
        call_kwargs = detect_api.deidentify_string.call_args[1]
        self.assertIsNotNone(call_kwargs['token_type'])
        self.assertEqual(call_kwargs['token_type']['default'], TokenType.VAULT_TOKEN)
        self.assertIn('vault_token', call_kwargs['token_type'])

    @patch("skyflow.vault.controller._detect.validate_deidentify_text_request")
    @patch("skyflow.vault.controller._detect.parse_deidentify_text_response")
    def test_deidentify_text_with_vault_token_specific_entities(self, mock_parse_response, mock_validate):
        """Test deidentify_text with VAULT_TOKEN for specific entities"""
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.data = {
            'text': '[SSN_VqLazzA] and [CREDIT_CARD]',
            'entities': []
        }

        # Create request with VAULT_TOKEN for specific entities
        request = DeidentifyTextRequest(
            text="My SSN is 123-45-6789 and my card is 4111 1111 1111 1111",
            entities=[DetectEntities.SSN, DetectEntities.CREDIT_CARD],
            token_format=TokenFormat(
                default=TokenType.ENTITY_ONLY,
                vault_token=[DetectEntities.SSN]
            )
        )

        # Mock detect API
        detect_api = self.vault_client.get_detect_text_api.return_value
        detect_api.deidentify_string.return_value = mock_api_response

        # Call deidentify_text
        response = self.detect.deidentify_text(request)

        # Assertions
        mock_validate.assert_called_once_with(self.vault_client.get_logger(), request)
        mock_parse_response.assert_called_once_with(mock_api_response)
        
        # Verify the API was called with vault_token list
        detect_api.deidentify_string.assert_called_once()
        call_kwargs = detect_api.deidentify_string.call_args[1]
        self.assertIsNotNone(call_kwargs['token_type'])
        self.assertEqual(call_kwargs['token_type']['default'], TokenType.ENTITY_ONLY)
        self.assertIn('vault_token', call_kwargs['token_type'])
        self.assertEqual(call_kwargs['token_type']['vault_token'], [DetectEntities.SSN])

    def test_get_token_format_with_vault_token(self):
        """Test __get_token_format includes vault_token field"""
        class DummyRequest:
            token_format = TokenFormat(
                default=TokenType.VAULT_TOKEN,
                vault_token=[DetectEntities.SSN, DetectEntities.CREDIT_CARD]
            )
        
        request = DummyRequest()
        result = self.detect._Detect__get_token_format(request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['default'], TokenType.VAULT_TOKEN)
        self.assertIn('vault_token', result)
        self.assertEqual(result['vault_token'], [DetectEntities.SSN, DetectEntities.CREDIT_CARD])

    def test_get_token_format_with_vault_token_only(self):
        """Test __get_token_format with only vault_token list"""
        class DummyRequest:
            token_format = TokenFormat(
                vault_token=[DetectEntities.SSN]
            )
        
        request = DummyRequest()
        result = self.detect._Detect__get_token_format(request)
        
        self.assertIsNotNone(result)
        self.assertIn('vault_token', result)
        self.assertEqual(result['vault_token'], [DetectEntities.SSN])

    @patch("skyflow.vault.controller._detect.validate_deidentify_file_request")
    @patch("skyflow.vault.controller._detect.base64")
    @patch("skyflow.vault.controller._detect.os.path.basename")
    def test_deidentify_file_with_vault_token(self, mock_basename, mock_base64, mock_validate):
        """Test deidentify_file with VAULT_TOKEN token format"""
        file_content = b"My SSN is 123-45-6789"
        file_obj = Mock()
        file_obj.read.return_value = file_content
        file_obj.name = "sensitive.txt"
        mock_basename.return_value = "sensitive.txt"
        mock_base64.b64encode.return_value = b"TXkgU1NOIGlzIDEyMy00NS02Nzg5"
        
        req = DeidentifyFileRequest(file=FileInput(file=file_obj))
        req.entities = [DetectEntities.SSN]
        req.token_format = TokenFormat(default=TokenType.VAULT_TOKEN)
        req.allow_regex_list = []
        req.restrict_regex_list = []
        req.transformations = None
        req.output_directory = None
        req.wait_time = None
        
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
        processed_response.word_character_count = WordCharacterCount(word_count=1, character_count=1)
        
        with patch.object(self.detect, "_Detect__poll_for_processed_file",
                          return_value=processed_response) as mock_poll, \
                patch.object(self.detect, "_Detect__parse_deidentify_file_response",
                             return_value=DeidentifyFileResponse(file_base64="base64",
                                                                 file=io.BytesIO(b"content"), type="txt",
                                                                 extension="txt",
                                                                 word_count=1, char_count=1, size_in_kb=1,
                                                                 duration_in_seconds=None, page_count=None,
                                                                 slide_count=None, entities=[], run_id="runid123",
                                                                 status="SUCCESS")) as mock_parse:
            result = self.detect.deidentify_file(req)
            
            mock_validate.assert_called_once()
            files_api.deidentify_text.assert_called_once()
            
            # Verify vault_token was included in the API call
            call_kwargs = files_api.deidentify_text.call_args[1]
            self.assertIsNotNone(call_kwargs['token_type'])
            self.assertIn('vault_token', call_kwargs['token_type'])
            self.assertEqual(call_kwargs['token_type']['default'], TokenType.VAULT_TOKEN)


if __name__ == '__main__':
    unittest.main()
