'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import unittest
import os

import aiohttp
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.vault import Client, Configuration, RedactionType
from skyflow.vault._get_by_id import createGetByIdResponseBody
from skyflow.service_account import generate_bearer_token
from dotenv import dotenv_values
import warnings
import asyncio
import json


class TestGetById(unittest.TestCase):

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
        return super().setUp()

    def add_mock_response(self, response, statusCode, table, encode=True):
        future = asyncio.Future(loop=self.event_loop)
        if encode:
            future.set_result(
                (json.dumps(response).encode(), statusCode, table))
        else:
            future.set_result((response, statusCode, table))
        future.done()
        self.mocked_futures.append(future)

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetByIdNoRecords(self):
        invalidData = {"invalidKey": "invalid"}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetByIdRecordsInvalidType(self):
        invalidData = {"records": "invalid"}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str))

    def testGetByIdNoIds(self):
        invalidData = {"records": [
            {"invalid": "invalid", "table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)

    def testGetByIdInvalidIdsType(self):
        invalidData = {"records": [
            {"ids": "invalid", "table": "pii_fields", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_IDS_TYPE.value % (str))

    def testGetByIdInvalidIdsType2(self):
        invalidData = {"records": [
            {"ids": ["123", 123], "table": "pii_fields", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_ID_TYPE.value % (int))

    def testGetByIdNoTable(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "invalid": "invalid", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testGetByIdInvalidTableType(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "table": ["invalid"], "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (list))

    def testGetByIdNoRedaction(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "table": "pii_fields", "invalid": "invalid"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.REDACTION_KEY_ERROR.value)

    def testGetByIdInvalidRedactionType(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "table": "pii_fields", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_REDACTION_TYPE.value % (str))

    def testCreateResponseBodySuccess(self):
        response = {"records": [
            {"fields": {"card_number": "4111-1111-1111-1111"}}]}
        self.add_mock_response(response, 200, "table")
        result, partial = createGetByIdResponseBody(self.mocked_futures)

        self.assertFalse(partial)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["fields"],
                         response["records"][0]["fields"])
        self.assertEqual(result["records"][0]["table"], "table")

    def testCreateResponseBodyPartialSuccess(self):
        success_response = {"records": [
            {"fields": {"card_number": "4111-1111-1111-1111"}}]}
        self.add_mock_response(success_response, 200, "table")

        failed_response = {"error": {
            "http_code": 404,
            "message": "Not Found"
        }}
        self.add_mock_response(failed_response, 404, "ok")

        result, partial = createGetByIdResponseBody(self.mocked_futures)

        self.assertTrue(partial)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["fields"],
                         success_response["records"][0]["fields"])
        self.assertEqual(result["records"][0]["table"], "table")

        self.assertTrue(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]['error']['code'],
                         failed_response["error"]['http_code'])
        self.assertEqual(result["errors"][0]['error']['description'],
                         failed_response["error"]['message'])

    def testCreateResponseBodyInvalidJson(self):
        response = "invalid json"
        self.add_mock_response(response.encode(), 200, 'table', encode=False)

        try:
            createGetByIdResponseBody(self.mocked_futures)
        except SkyflowError as error:
            expectedError = SkyflowErrorMessages.RESPONSE_NOT_JSON
            self.assertEqual(error.code, 200)
            self.assertEqual(error.message, expectedError.value % response)

    def testGetByIdNoColumnName(self):
        invalidData = {"records": [
            {"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)
    
    def testGetByIdInvalidColumnName(self):
        invalidData = {"records": [
            {"ids": ["123", "456"],"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": ["invalid"]}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_COLUMN_NAME.value % (list))
    
    def testGetByIdNoColumnValues(self):
        invalidData = {"records": [
            {"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": "first_name"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)

    def testGetByIdInvalidColumnValues(self):
        invalidData = {"records": [
            {"ids": ["123", "456"], "table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": "first_name", "columnValues": "invalid"}]}
        try:
            self.client.get_by_id(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_COLUMN_VALUE.value % (str))
    
    def testGet(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "invalid": "invalid", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)