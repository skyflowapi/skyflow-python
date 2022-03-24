import unittest
import os
from skyflow.vault._detokenize import getDetokenizeRequestBody
from skyflow.errors._skyflowerrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.vault._client import Client, Configuration
from skyflow.service_account import generate_bearer_token
from dotenv import dotenv_values
import warnings


class TestDetokenize(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        self.testToken = self.envValues["DETOKENIZE_TEST_TOKEN"]
        self.tokenField = {
            "token": self.envValues["DETOKENIZE_TEST_TOKEN"]
        }
        self.data = {"records": [self.tokenField]}

        def tokenProvider():
            token, type = generate_bearer_token(
                self.envValues["CREDENTIALS_FILE_PATH"])
            return token

        config = Configuration(
            self.envValues["VAULT_ID"], self.envValues["VAULT_URL"], tokenProvider)
        self.client = Client(config)
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning)
        return super().setUp()

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
