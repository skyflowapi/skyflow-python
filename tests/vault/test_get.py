'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import unittest
import os

from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.vault import Client, Configuration, RedactionType, GetOptions
from skyflow.service_account import generate_bearer_token
from dotenv import dotenv_values
import warnings
import asyncio
import json


class TestGet(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/test_get.py')
        self.event_loop = asyncio.new_event_loop()
        self.mocked_futures = []

        def tokenProvider():
            # filePath = "credentials.json"
            token, type = generate_bearer_token(
                self.envValues["CREDENTIALS_FILE_PATH"])
                # self.envValues[filePath])
            return token

        config = Configuration(
            self.envValues["VAULT_ID"], self.envValues["VAULT_URL"], tokenProvider)
            # self.envValues["e80f3623b8ef4f57bcedb6619075fcff"], self.envValues["https://sb.area51.vault.skyflowapis.dev"], tokenProvider)
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
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetByIdRecordsInvalidType(self):
        invalidData = {"records": "invalid"}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str))

    def testGetByIdNoIds(self):
        invalidData = {"records": [
            # {"invalid": "invalid", "table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT}]}
            {"invalid": "invalid", "table": "newstripe", "redaction": RedactionType.PLAIN_TEXT}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)

    def testGetByIdInvalidIdsType(self):
        invalidData = {"records": [
            # {"ids": "invalid", "table": "pii_fields", "redaction": "PLAIN_TEXT"}]}
            {"ids": "invalid", "table": "newstripe", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_IDS_TYPE.value % (str))

    def testGetByIdInvalidIdsType2(self):
        invalidData = {"records": [
            # {"ids": ["123", 123], "table": "pii_fields", "redaction": "PLAIN_TEXT"}]}
            {"ids": ["123", 123], "table": "newstripe", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_ID_TYPE.value % (int))

    def testGetByIdNoTable(self):
        invalidData = {"records": [
            {"ids": ["id1", "id2"], "invalid": "invalid", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testGetByIdInvalidTableType(self):
        invalidData = {"records": [
            # {"ids": ["id1", "id2"], "table": ["invalid"], "redaction": "PLAIN_TEXT"}]}
            {"ids": ["id1", "id2"], "table": ["invalid"], "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (list))

    def testGetByIdNoColumnName(self):
        invalidData = {"records": [
            # {"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT}]}
            {"table": "newstripe", "redaction": RedactionType.PLAIN_TEXT}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)

    def testGetByIdInvalidColumnName(self):
        invalidData = {"records": [
            # {"ids": ["123", "456"],"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": ["invalid"]}]}
              {"ids": ["123", "456"], "table": "newstripe", "redaction": RedactionType.PLAIN_TEXT,
             "columnName": ["invalid"]}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_COLUMN_NAME.value % (list))

    def testGetByIdNoColumnValues(self):
        invalidData = {"records": [
            # {"table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": "first_name"}]}
            {"table": "newstripe", "redaction": RedactionType.PLAIN_TEXT, "columnName": "card_number"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.UNIQUE_COLUMN_OR_IDS_KEY_ERROR.value)

    def testGetByIdInvalidColumnValues(self):
        invalidData = {"records": [
            # {"ids": ["123", "456"], "table": "pii_fields", "redaction": RedactionType.PLAIN_TEXT, "columnName": "first_name", "columnValues": "invalid"}]}
            {"ids": ["123", "456"], "table": "newstripe", "redaction": RedactionType.PLAIN_TEXT,
             "columnName": "card_number", "columnValues": "invalid"}]}
        try:
            self.client.get(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_COLUMN_VALUE.value % (str) )


    def testGetByTokenAndRedaction(self):
        invalidData = {"records": [
            {"ids": ["123","456"],
             "table": "stripe", "redaction": RedactionType.PLAIN_TEXT,}]}
        options = GetOptions(True)
        try:
            self.client.get(invalidData,options=options)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.REDACTION_WITH_TOKENS_NOT_SUPPORTED.value)

    def testGetByNoOptionAndRedaction(self):
        invalidData = {"records":[
            {"ids":["123","456"],"table":"newstripe"}]}
        options = GetOptions(False)
        try:
            self.client.get(invalidData,options=options)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code,SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message,SkyflowErrorMessages.REDACTION_KEY_ERROR.value)

    def testGetByOptionAndUniqueColumnRedaction(self):
        invalidData ={"records":[
            {"table":"newstripe","columnName":"card_number","columnValues":["456","980"],}
        ]}

        options = GetOptions(True)
        try:
            self.client.get(invalidData, options=options)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.TOKENS_GET_COLUMN_NOT_SUPPORTED.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKENS_GET_COLUMN_NOT_SUPPORTED.value)
