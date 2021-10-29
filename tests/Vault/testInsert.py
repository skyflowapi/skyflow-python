import json
import unittest
import os
from requests.models import Response
from skyflow.Vault._insert import getInsertRequestBody, processResponse
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages

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
        body = json.loads(getInsertRequestBody(self.data))
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
            getInsertRequestBody(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

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
            getInsertRequestBody(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.FIELDS_KEY_ERROR.value)


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
            getInsertRequestBody(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

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
            getInsertRequestBody(invalidjson)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_JSON.value%('insert payload'))

    def testProcessInvalidResponse(self):
        response = Response()
        response.status_code = 500
        response._content = b"Invalid Request"
        try:
            processResponse(response, True)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, 500)
            self.assertEqual(e.message, response.content.decode('utf-8'))

    def testProcessInvalidResponse(self):
        response = Response()
        response.status_code = 200
        response._content = b'{"key": "value"}'
        try:
            processedResponse = processResponse(response, True)
            responseDict = json.loads(processedResponse)
            self.assertDictEqual(responseDict, {'key': 'value'})
        except SkyflowError as e:
            self.fail

    # def testClientInsert(self):
    #     def tokenProvider():
            # token, type = GenerateToken(self.getDataPath('credentials'))
    #         return "token"
    #     client = Client('bdc271aee8584eed88253877019657b3', 'https://sb.area51.vault.skyflowapis.dev', tokenProvider)

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
    #         print(client.insert(data))
    #     except SkyflowError as e:
    #         print(e)

