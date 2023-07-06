import json
import unittest
import os

import asyncio
import warnings
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
            self.envValues["VAULT_ID"], self.envValues["VAULT_URL"], tokenProvider)
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

    def testDeleteByIdInvalidIdsType(self):
        invalidData = {"records": [
            {"ids": "invalid", "table": "stripe"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_IDS_TYPE.value % (str))

    def testDeleteByIdNoTable(self):
        invalidData = {"records": [
            {"ids": ["id1"], "invalid": "invalid"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testDeleteByIdInvalidTableType(self):
        invalidData = {"records": [
            {"ids": ["id1"], "table": ["invalid"]}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (list))

    def deleteProcessResponse(response: requests.Response, interface=None):
        statusCode = response.status_code
        content = response.content.decode('utf-8')
        try:
            response.raise_for_status()
            if statusCode == 204:
                return None
            try:
                return json.loads(content)
            except:
                raise SkyflowError(
                    statusCode, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content, interface=interface)
        except HTTPError:
            message = SkyflowErrorMessages.API_ERROR.value % statusCode
            if content is not None:
                try:
                    errorResponse = json.loads(content)
                    if 'error' in errorResponse and type(errorResponse['error']) == dict and 'message' in errorResponse[
                        'error']:
                        message = errorResponse['error']['message']
                except:
                    message = SkyflowErrorMessages.RESPONSE_NOT_JSON.value % content
            error = {}
            if 'x-request-id' in response.headers:
                message += ' - request id: ' + response.headers['x-request-id']
                error.update({"code": statusCode, "description": message})
            return error