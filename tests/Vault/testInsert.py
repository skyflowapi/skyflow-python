import json
import unittest
import os
from requests.models import Response
from dotenv import dotenv_values
from skyflow.Vault._insert import getInsertRequestBody, processResponse
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.ServiceAccount import generateBearerToken
from skyflow.Vault._client import Client
from skyflow.Vault._config import Configuration, InsertOptions

class TestInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/Vault/data/')
        field = {
            "table": "persons",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }
        }
        self.data = {"records": [field]}
        return super().setUp()


    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetInsertRequestBodyWithValidBody(self):
        body = json.loads(getInsertRequestBody(self.data, True))
        expectedOutput = {
            "tableName": "persons",
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
            self.assertEqual(e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetInsertRequestBodyRecordsInvalidType(self):
        invalidData = {"records": 'records'}
        try:
            getInsertRequestBody(invalidData, True)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value % (str(type('str'))))

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
            self.assertEqual(e.message, SkyflowErrorMessages.FIELDS_KEY_ERROR.value)

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
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value % (str(type('str'))))


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
            self.assertEqual(e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

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
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (str(type({'a': 'b'}))))

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
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_JSON.value%('insert payload'))

    def testProcessInvalidResponse(self):
        response = Response()
        response.status_code = 500
        response._content = b"Invalid Request"
        try:
            processResponse(response)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, 500)
            self.assertEqual(e.message, response.content.decode('utf-8'))

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
        config = Configuration('vaultid', 'https://skyflow.com', lambda: 'test')
        client = Client(config)
        self.assertEqual(client.vaultURL, 'https://skyflow.com')
        self.assertEqual(client.vaultID, 'vaultid')
        self.assertEqual(client.tokenProvider(), 'test')

    # def testClientInsert(self):
    #     env_values = dotenv_values('.env')

    #     def tokenProvider():
    #         token, _ = generateBearerToken(env_values['CREDENTIALS_FILE_PATH'])
    #         return token

    #     config = Configuration(env_values['VAULT_ID'], env_values['VAULT_URL'], tokenProvider)
    #     client = Client(config)

    #     options = InsertOptions(False)

    #     data = {
    #         "records": [
    #             {
    #                 "table": "persons",
    #                 "fields": {
    #                     "cvv": "122",
    #                     "card_expiration": "1221",
    #                     "card_number": "4111111111111111",
    #                     "name": {"first_name": "Bob"}
    #                 }
    #             }
    #         ]
    #     }
    #     try:
    #         response = client.insert(data, options=options)
    #         self.assertEqual(len(response['records']), 1)
    #     except SkyflowError as e:
    #         self.fail()

    # def testClientInsertWithTokens(self):
    #     env_values = dotenv_values('.env')

    #     def tokenProvider():
    #         token, _ = generateBearerToken(env_values['CREDENTIALS_FILE_PATH'])
    #         return token

    #     config = Configuration(env_values['VAULT_ID'], env_values['VAULT_URL'], tokenProvider)
    #     client = Client(config)

    #     options = InsertOptions(True)

    #     data = {
    #         "records": [
    #             {
    #                 "table": "persons",
    #                 "fields": {
    #                     "cvv": "122",
    #                     "card_expiration": "1221",
    #                     "card_number": "4111111111111111",
    #                     "name": {"first_name": "Bob"}
    #                 }
    #             }
    #         ]
    #     }
    #     try:
    #         response = client.insert(data, options=options)
    #         self.assertEqual(len(response['records']), 1)
    #     except SkyflowError as e:
    #         self.fail()
