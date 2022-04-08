import unittest
import os
from skyflow.vault._detokenize import getDetokenizeRequestBody, createDetokenizeResponseBody
from skyflow.errors._skyflowerrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.vault._client import Client, Configuration
from skyflow.service_account import generate_bearer_token
from dotenv import dotenv_values
import warnings

import json
import asyncio


class TestDetokenize(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        self.testToken = self.envValues["DETOKENIZE_TEST_TOKEN"]
        self.tokenField = {
            "token": self.envValues["DETOKENIZE_TEST_TOKEN"]
        }
        self.data = {"records": [self.tokenField]}
        self.mocked_futures = []
        self.event_loop = asyncio.new_event_loop()

        def tokenProvider():
            token, _ = generate_bearer_token(
                self.envValues["CREDENTIALS_FILE_PATH"])
            return token

        config = Configuration(
            self.envValues["VAULT_ID"], self.envValues["VAULT_URL"], tokenProvider)
        self.client = Client(config)
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning)
        return super().setUp()

    def add_mock_response(self, response, statusCode):
        future = asyncio.Future(loop=self.event_loop)
        future.set_result((json.dumps(response).encode(), statusCode))
        future.done()
        self.mocked_futures.append(future)

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetDetokenizeRequestBodyWithValidBody(self):
        body = getDetokenizeRequestBody(self.tokenField)
        expectedOutput = {
            "detokenizationParameters": [{
                "token": self.testToken
            }]
        }

        self.assertEqual(body, expectedOutput)

    def testDetokenizeNoRecords(self):
        invalidData = {"invalidKey": self.tokenField}
        try:
            self.client.detokenize(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testDetokenizeRecordsInvalidType(self):
        invalidData = {"records": "invalid"}
        try:
            self.client.detokenize(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str))

    def testDetokenizeNoToken(self):
        invalidData = {"records": [{"invalid": "invalid"}]}
        try:
            self.client.detokenize(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKEN_KEY_ERROR.value)

    def testDetokenizeTokenInvalidType(self):
        invalidData = {"records": [{"token": ["invalid"]}]}
        try:
            self.client.detokenize(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TOKEN_TYPE.value % (list))

    def testDetokenizeSuccess(self):
        data = {"records": [
            {"token": self.envValues["DETOKENIZE_TEST_TOKEN"]}]}
        try:
            response = self.client.detokenize(data)
            self.assertEqual(
                response["records"][0]["token"], self.envValues["DETOKENIZE_TEST_TOKEN"])
            self.assertEqual(
                response["records"][0]["value"], self.envValues["DETOKENIZE_TEST_VALUE"])
        except SkyflowError as e:
            self.fail('Should not throw an error')

    def testDetokenizePartialSuccess(self):
        data = {"records": [{"token": self.envValues["DETOKENIZE_TEST_TOKEN"]}, {
            "token": "invalid-token"}]}
        try:
            self.client.detokenize(data)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.PARTIAL_SUCCESS.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.PARTIAL_SUCCESS.value)
            self.assertEqual(e.data["records"][0]["token"],
                             self.envValues["DETOKENIZE_TEST_TOKEN"])
            self.assertEqual(e.data["records"][0]["value"],
                             self.envValues["DETOKENIZE_TEST_VALUE"])
            self.assertEqual(e.data["errors"][0]["error"]["code"], 404)
            self.assertTrue(e.data["errors"][0]["error"]["description"].find(
                "Token not found for invalid-token") != -1)

    def testResponseBodySuccess(self):
        response = {"records": [{"token": "abc", "value": "secret"}]}
        self.add_mock_response(response, 200)
        res, partial = createDetokenizeResponseBody(self.mocked_futures)
        self.assertEqual(partial, False)
        self.assertEqual(res, {"records": response["records"], "errors": []})

    def testResponseBodyPartialSuccess(self):
        success_response = {"records": [{"token": "abc", "value": "secret"}]}
        error_response = {"error": {"http_code": 404, "message": "not found"}}
        self.add_mock_response(success_response, 200)
        self.add_mock_response(error_response, 404)
        res, partial = createDetokenizeResponseBody(self.mocked_futures)
        self.assertTrue(partial)
        self.assertEqual(res["records"], success_response["records"])
        errors = res["errors"]

        self.assertIsNotNone(errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"]["code"],
                         error_response["error"]["http_code"])
        self.assertEqual(
            errors[0]["error"]["description"], error_response["error"]["message"])
