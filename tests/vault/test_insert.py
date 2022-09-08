'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import unittest
import os
from requests.models import Response
from dotenv import dotenv_values
from skyflow.vault._insert import getInsertRequestBody, processResponse, convertResponse
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.service_account import generate_bearer_token
from skyflow.vault._client import Client
from skyflow.vault._config import Configuration, InsertOptions


class TestInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        record = {
            "table": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }
        }
        self.data = {"records": [record]}
        self.mockRequest = {"records": [record]}

        self.mockResponse = {"responses": [
            {
                "records": [{"skyflow_id": 123}],
                "table": "pii_fields"
            },
            {
                "fields": {
                    "cardNumber": "card_number_token",
                    "cvv": "cvv_token"
                }
            }
        ]}

        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetInsertRequestBodyWithValidBody(self):
        body = json.loads(getInsertRequestBody(self.data, True))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "method": 'POST',
            "quorum": True
        }
        self.assertEqual(body["records"][0], expectedOutput)

    def testGetInsertRequestBodyNoRecords(self):
        invalidData = {"invalidKey": self.data["records"]}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetInsertRequestBodyRecordsInvalidType(self):
        invalidData = {"records": 'records'}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str(type('str'))))

    def testGetInsertRequestBodyNoFields(self):
        invalidData = {"records": [{
            "table": "table",
            "fields": {
                "card_number": "4111-1111"
            }
        },
            {
            "table": "table",
            "invalid": {}
        }
        ]}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FIELDS_KEY_ERROR.value)

    def testGetInsertRequestBodyInvalidFieldsType(self):
        invalidData = {"records": [{
            "table": "table",
            "fields": 'fields'
        }
        ]}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value % (str(type('str'))))

    def testGetInsertRequestBodyNoTable(self):
        invalidData = {"records": [{
            "noTable": "tableshouldbehere",
            "fields": {
                "card_number": "4111-1111"
            }
        },
            {
            "table": "table",
            "invalid": {}
        }
        ]}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testGetInsertRequestBodyInvalidTableType(self):
        invalidData = {"records": [{
            "table": {'invalidtype': 'thisisinvalid'},
            "fields": {
                "card_number": "4111-1111"
            }
        }
        ]}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
                str(type({'a': 'b'}))))

    def testInsertInvalidJson(self):
        invalidjson = {
            "records": [{
                "table": "table",
                "fields": {
                    "invalid": json
                }
            }]
        }

        try:
            getInsertRequestBody(invalidjson, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_JSON.value % ('insert payload'))

    def testProcessInvalidResponse(self):
        response = Response()
        response.status_code = 500
        response._content = b"Invalid Request"
        try:
            processResponse(response)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, 500)
            self.assertEqual(e.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value %
                             response.content.decode('utf-8'))

    def testProcessValidResponse(self):
        response = Response()
        response.status_code = 200
        response._content = b'{"key": "value"}'
        try:
            responseDict = processResponse(response)
            self.assertDictEqual(responseDict, {'key': 'value'})
        except SkyflowError as e:
            self.fail()

    def testClientInit(self):
        config = Configuration(
            'vaultid', 'https://skyflow.com', lambda: 'test')
        client = Client(config)
        self.assertEqual(client.vaultURL, 'https://skyflow.com')
        self.assertEqual(client.vaultID, 'vaultid')
        self.assertEqual(client.tokenProvider(), 'test')

    def testProcessResponseInvalidJson(self):
        invalid_response = Response()
        invalid_response.status_code = 200
        invalid_response._content = b'invalid-json'
        try:
            processResponse(invalid_response)
            self.fail('not failing on invalid json')
        except SkyflowError as se:
            self.assertEqual(se.code, 200)
            self.assertEqual(
                se.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % 'invalid-json')

    def testProcessResponseFail(self):
        invalid_response = Response()
        invalid_response.status_code = 404
        invalid_response._content = b"error"
        try:
            processResponse(invalid_response)
            self.fail('Not failing on invalid error json')
        except SkyflowError as se:
            self.assertEqual(se.code, 404)
            self.assertEqual(
                se.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % 'error')

    def testConvertResponseNoTokens(self):
        tokens = False
        result = convertResponse(self.mockRequest, self.mockResponse, tokens)

        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["skyflow_id"], 123)
        self.assertEqual(result["records"][0]["table"], "pii_fields")
        self.assertNotIn("fields", result["records"][0])

    def testConvertResponseWithTokens(self):
        tokens = True
        result = convertResponse(self.mockRequest, self.mockResponse, tokens)

        self.assertEqual(len(result["records"]), 1)
        self.assertNotIn("skyflow_id", result["records"][0])
        self.assertEqual(result["records"][0]["table"], "pii_fields")

        self.assertIn("fields", result["records"][0])
        self.assertEqual(result["records"][0]["fields"]["skyflow_id"], 123)

        self.assertEqual(result["records"][0]["fields"]
                         ["cardNumber"], "card_number_token")
        self.assertEqual(result["records"][0]["fields"]
                         ["cvv"], "cvv_token")

    def testInsertInvalidToken(self):
        config = Configuration('id', 'url', lambda: 'invalid-token')
        try:
            Client(config).insert({'records': []})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKEN_PROVIDER_INVALID_TOKEN.value)
