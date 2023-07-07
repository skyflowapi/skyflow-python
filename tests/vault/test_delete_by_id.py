import json
import unittest
import os

import asyncio
import warnings
from unittest import mock
from unittest.mock import patch, MagicMock

import requests
from requests import HTTPError
from requests.models import Response
from dotenv import dotenv_values

from skyflow.errors import SkyflowError, SkyflowErrorCodes
from skyflow.errors._skyflow_errors import SkyflowErrorMessages
from skyflow.service_account import generate_bearer_token
from skyflow.vault._client import Client
from skyflow.vault._config import Configuration,DeleteOptions
from skyflow.vault._delete_by_id import deleteProcessResponse


class TestDelete(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        self.event_loop = asyncio.new_event_loop()
        self.mocked_futures = []

        def tokenProvider():
            token, type = generate_bearer_token(
                self.envValues["CREDENTIALS_FILE_PATH"])
            return token

        config = Configuration(
            "12345", "demo", tokenProvider)
        self.client = Client(config)
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning)

        self.record_id = "123"

        self.mockResponse = {
            "responses": [
                {
                    "records": [
                        {
                            "skyflow_id": self.record_id,
                            "deleted": True
                        }
                    ]
                }
            ]
        }
        self.DeleteOptions = DeleteOptions(tokens=False)

        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testDeleteByIdInvalidIdType(self):
        invalidData = {"records": [
            {"id": "invalid", "table": "stripe"}]}
        try:
            self.client.delete_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_IDS_TYPE.value)

    def testDeleteByIdNoId(self):
        invalidData = {"records": [
            {"invalid": "invalid", "table": "stripe"}]}
        try:
            self.client.delete_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.IDS_KEY_ERROR.value)

    def testDeleteByIdNoTable(self):
        invalidData = {"records": [
            {"id": ["id1"], "invalid": "invalid"}]}
        try:
            self.client.delete_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testDeleteByIdInvalidTableType(self):
        invalidData = {"records": [
            {"id": ["id1"], "table": ["invalid"]}]}
        try:
            self.client.delete_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value)

    def testDeleteProcessResponseWithSuccessfulResponse(self):
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"key": "value"}'
        result = deleteProcessResponse(mock_response)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {"key": "value"})

    def testDeleteProcessResponseWithNoContentResponse(self):
        mock_response = requests.Response()
        mock_response.status_code = 204
        result = deleteProcessResponse(mock_response)
        self.assertIsNone(result)

    def test_http_error_with_error_message(self):
        error_response = {
                'code': 400,
                'description': 'Error occurred'
            }
        response = mock.Mock(spec=requests.Response)
        response.status_code = 400
        response.content = json.dumps(error_response).encode()
        error = deleteProcessResponse(response)
        self.assertEqual(error, {
            "code": 400,
            "description": "Error occurred",
        })

    def test_delete_data_success(self):
        records = {"records": [
            {"id": ["id1"], "table": "stripe"}]}
        self.mock_response = mock.Mock(spec=requests.Response)
        self.mock_response.status_code = 204
        self.mock_response.content = b''
        with mock.patch('requests.delete', return_value=self.mock_response):
            result = self.client.delete_by_id(records)
        self.assertIn('records', result)
        self.assertEqual(result['records'], [None])

    def test_delete_data_with_errors(self):
        response = mock.Mock(spec=requests.Response)
        response.status_code = 404
        response.content = b'{"code": 404, "description": "Not found"}'
        with mock.patch('requests.delete', return_value=response):
            records = {"records": [
                {"id": ["id1"], "table": "stripe"},
            ]}
            result = self.client.delete_by_id(records)

        self.assertIn('errors', result)
        error = result['errors'][0]
        self.assertEqual(error['id'], "id1")
        self.assertEqual(error['error'], {'code': 404, 'description': 'Not found'})

    def testDeleteProcessInvalidResponse(self):
        response = Response()
        response.status_code = 500
        response._content = b"Invalid Request"
        try:
            deleteProcessResponse(response)
        except SkyflowError as e:
            self.assertEqual(e.code, 500)
            self.assertEqual(e.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value %
                             response.content.decode('utf-8'))