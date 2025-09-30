'''
    Copyright (c) 2022 Skyflow, Inc.
'''
import json
import unittest
from unittest.mock import Mock, patch, ANY
import os
from dotenv import dotenv_values
import requests
from requests.models import Response
from skyflow.errors._skyflow_errors import SkyflowError
from skyflow.vault._client import Client
from skyflow.vault._config import Configuration, InsertOptions, BYOT

class TestInsertWithMocks(unittest.TestCase):
    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        self.valid_token = self.envValues["MOCK_TOKEN"]
        self.record = {
            "table": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }
        }
        self.data = {"records": [self.record, self.record]}
        
        # Mock API response data
        self.mock_success_response = {
            "responses": [
                {
                    "records": [
                        {
                            "skyflow_id": "123",
                            "tokens": {
                                "cardNumber": "card_number_token",
                                "cvv": "cvv_token"
                            }
                        }
                    ]
                },
                {
                    "records": [
                        {
                            "skyflow_id": "456",
                            "tokens": {
                                "cardNumber": "card_number_token",
                                "cvv": "cvv_token"
                            }
                        }
                    ]
                },
            ],
            "requestId": "test-request-id"
        }

        self.mock_error_response = {
            "error": {
                "grpc_code": 3,
                "http_code": 400,
                "message": "Insert failed due to error.",
                "http_status": "Bad Request"
            }
        }

        # Create configurations for testing with different token scenarios
        self.valid_config = Configuration(
            'test-vault-id',
            'https://test-vault.skyflow.com',
            lambda: self.valid_token
        )
        
        self.invalid_config = Configuration(
            'test-vault-id',
            'https://test-vault.skyflow.com',
            lambda: 'invalid-token'
        )

    @patch('requests.post')
    def test_successful_insert(self, mock_post):
        # Setup mock response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.content = json.dumps(self.mock_success_response).encode('utf-8')
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_post.return_value = mock_response        # Create client and perform insert
        client = Client(self.valid_config)
        options = InsertOptions(tokens=True)
        result = client.insert(self.data, options)

        # Verify the result
        self.assertIn("records", result)
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["fields"]["cardNumber"], "card_number_token")
        
        # Verify the API was called with correct parameters
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertTrue(called_url.endswith("/v1/vaults/test-vault-id"))

    @patch('requests.post')
    def test_insert_api_error(self, mock_post):
        # Setup mock error response
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_response.content = json.dumps(self.mock_error_response).encode('utf-8')
        mock_response.headers = {'x-request-id': 'test-request-id'}
        
        # Mock raise_for_status to raise HTTPError
        def raise_for_status():
            raise requests.exceptions.HTTPError("400 Client Error")
        mock_response.raise_for_status = raise_for_status
        
        mock_post.return_value = mock_response

        # Create client and attempt insert
        client = Client(self.valid_config)
        options = InsertOptions(tokens=True)
        
        # This should raise a SkyflowError
        with self.assertRaises(SkyflowError) as context:
            client.insert(self.data, options)
            
        # Verify the error details
        self.assertEqual(context.exception.code, 400)
        self.assertIn("Insert failed due to error", context.exception.message)

    @patch('requests.post')
    def test_insert_network_error(self, mock_post):
        # Setup mock to simulate network error
        mock_post.side_effect = Exception("Network error")

        # Create client and attempt insert
        client = Client(self.valid_config)
        options = InsertOptions(tokens=True)

        # Assert that the insert raises an error
        with self.assertRaises(SkyflowError) as context:
            client.insert(self.data, options)

    @patch('requests.post')
    def test_insert_with_continue_on_error_partial_sucess(self, mock_post):
        # Setup mock response with partial success
        partial_response = {
            "responses": [
                {
                    "Body": {
                        "records": [
                            {
                                "skyflow_id": "123",
                                "tokens": {"cardNumber": "token1"}
                            }
                        ]
                    },
                    "Status": 200
                },
                {
                    "Body": {
                        "error": "Unique constraint violation"
                    },
                    "Status": 400
                }
            ],
            "requestId": "test-request-id"
        }
        
        mock_response = Mock(spec=Response)
        mock_response.status_code = 207
        mock_response.content = json.dumps(partial_response).encode('utf-8')
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_post.return_value = mock_response

        # Create client and perform insert with continueOnError
        client = Client(self.valid_config)
        options = InsertOptions(tokens=True, continueOnError=True)
        
        # Create test data with two records
        test_data = {
            "records": [
                self.record,
                self.record  # Duplicate record that will cause error
            ]
        }
        
        result = client.insert(test_data, options)

        # Verify partial success results
        self.assertIn("records", result)
        self.assertIn("errors", result)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    @patch('requests.post')
    def test_insert_with_continue_on_error_complete_failure(self, mock_post):
        # Setup mock response with complete failure
        complete_failure_response = {
            "responses": [
                {
                    "Body": {
                        "error": "Unique constraint violation"
                    },
                    "Status": 400
                },
                {
                    "Body": {
                        "error": "Unique constraint violation"
                    },
                    "Status": 400
                }
            ],
            "requestId": "test-request-id"
        }

        mock_response = Mock(spec=Response)
        mock_response.status_code = 207
        mock_response.content = json.dumps(complete_failure_response).encode('utf-8')
        mock_response.headers = {'x-request-id': 'test-request-id'}
        mock_post.return_value = mock_response

        # Create client and perform insert with continueOnError
        client = Client(self.valid_config)
        options = InsertOptions(tokens=True, continueOnError=True)

        # Create test data with two records
        test_data = {
            "records": [
                self.record,
                self.record  # Duplicate record that will cause error
            ]
        }

        result = client.insert(test_data, options)

        # Verify complete failure results
        self.assertIn("errors", result)
        self.assertNotIn("records", result)
        self.assertEqual(len(result["errors"]), 2)

