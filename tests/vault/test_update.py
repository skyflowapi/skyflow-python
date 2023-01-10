'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import unittest
import os
import asyncio
import warnings

from dotenv import dotenv_values
from skyflow.vault._client import Client, Configuration
from skyflow.vault._update import sendUpdateRequests, createUpdateResponseBody
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.service_account import generate_bearer_token
from skyflow.vault._client import Client
from skyflow.vault._config import UpdateOptions


class TestUpdate(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
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
    
    def add_mock_response(self, response, statusCode, encode=True):
        future = asyncio.Future(loop=self.event_loop)
        if encode:
            future.set_result((json.dumps(response).encode(), statusCode))
        else:
            future.set_result((response, statusCode))
        future.done()
        self.mocked_futures.append(future)

    def getDataPath(self, file):
        return self.dataPath + file + '.json'
    
    def testUpdateNoRecords(self):
        invalidData = {}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testUpdateInvalidType(self):
        invalidData = {"records": "invalid"}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str))
    
    def testUpdateNoIds(self):
        invalidData = {"records": [
            {"table": "pii_fields"}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.IDS_KEY_ERROR.value)
    
    def testUpdateInvalidIdType(self):
        invalidData = {"records": [
            {"id": ["123"], "table": "pii_fields"}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_ID_TYPE.value % (list))

    def testUpdateNoTable(self):
        invalidData = {"records": [
            {"id": "id"}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testUpdateInvalidTableType(self):
        invalidData = {"records": [
            {"id": "id1", "table": ["invalid"]}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (list))
    
    def testUpdateNoFields(self):
        invalidData = {"records": [
            {"id": "id", "table": "pii_fields"}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FIELDS_KEY_ERROR.value)

    def testUpdateInvalidFieldsType(self):
        invalidData = {"records": [
            {"id": "id1", "table": "pii_fields", "fields": "invalid"}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value % (str))
    
    def testUpdateInvalidFieldsType2(self):
        invalidData = {"records": [
            {"id": "id1", "table": "pii_fields", "fields": {}}]}
        try:
            self.client.update(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UPDATE_FIELD_KEY_ERROR.value)

    def testResponseBodySuccess(self):
        response = {"skyflow_id": "123", "tokens": {"first_name": "John"}}
        mock_response = [{"id": "123", "fields": {"first_name": "John"}}]
        self.add_mock_response(response, 200)
        print("Seld.mockedFuturs", self.mocked_futures)
        res, partial = createUpdateResponseBody(self.mocked_futures)
        self.assertEqual(partial, False)
        self.assertEqual(res, {"records": mock_response, "errors": []})

    def testResponseBodyPartialSuccess(self):
        success_response = {"skyflow_id": "123", "tokens": {"first_name": "John"}}
        mock_success_response = [{"id": "123", "fields": {"first_name": "John"}}]
        error_response = {"error": {"http_code": 404, "message": "not found"}}
        self.add_mock_response(success_response, 200)
        self.add_mock_response(error_response, 404)
        res, partial = createUpdateResponseBody(self.mocked_futures)
        self.assertTrue(partial)
        self.assertEqual(res["records"], mock_success_response)
        errors = res["errors"]

        self.assertIsNotNone(errors)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"]["code"],
                         error_response["error"]["http_code"])
        self.assertEqual(
            errors[0]["error"]["description"], error_response["error"]["message"])

    def testResponseNotJson(self):
        response = "not a valid json".encode()
        self.add_mock_response(response, 200, encode=False)
        try:
            createUpdateResponseBody(self.mocked_futures)
        except SkyflowError as error:
            expectedError = SkyflowErrorMessages.RESPONSE_NOT_JSON
            self.assertEqual(error.code, 200)
            self.assertEqual(error.message, expectedError.value %
                             response.decode('utf-8'))
