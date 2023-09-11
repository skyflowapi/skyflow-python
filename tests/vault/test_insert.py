'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import unittest
import os
from requests.models import Response
from dotenv import dotenv_values
from skyflow.vault._insert import getInsertRequestBody, processResponse, convertResponse, getUpsertColumn, validateUpsertOptions
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.service_account import generate_bearer_token
from skyflow.vault._client import Client
from skyflow.vault._config import Configuration, InsertOptions, UpsertOption, BYOT


class TestInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        record = {
            "table": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "tokens":{
                "cardNumber": "4111-1111-1111-1111",
            }
        }
        self.data = {"records": [record]}
        self.mockRequest = {"records": [record]}
        record2 = {
            "table": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }
        }
        self.data2 = {"records": [record2]}
        self.mockRequest2 = {"records": [record2]}

        self.mockResponse = {
            "responses": [
                {
                    "records": [
                        {
                            "skyflow_id": 123,
                            "tokens": {
                                "first_name": "4db12c22-758e-4fc9-b41d-e8e48b876776",
                                "cardNumber": "card_number_token",
                                "cvv": "cvv_token",
                                "expiry_date": "6b45daa3-0e81-42a8-a911-23929f1cf9da"
            
                            }
                        }
                    ],
                }
            ],
            "requestId": "2g3fd14-z9bs-xnvn4k6-vn1s-e28w35"
        }
        
        self.mockResponseCOESuccessObject = {
            "Body": {
                "records": self.mockResponse['responses'][0]['records']
            },
            "Status": 200
        }
        
        self.mockResponseCOEErrorObject = {
            "Body": {
                "error": "Error Inserting Records due to unique constraint violation"
            },
            "Status": 400
        }
        
        self.mockResponseCOESuccess = {
            "responses": [self.mockResponseCOESuccessObject],
            "requestId": self.mockResponse['requestId']
        }
        
        self.mockResponseCOEPartialSuccess = {
            "responses": [
                self.mockResponseCOESuccessObject,
                self.mockResponseCOEErrorObject
            ],
            "requestId": self.mockResponse['requestId']
        }
        
        self.mockResponseCOEFailure = {
            "responses": [self.mockResponseCOEErrorObject],
            "requestId": self.mockResponse['requestId']
        }
        
        self.insertOptions = InsertOptions(tokens=True)
        self.insertOptions2 = InsertOptions(tokens=True, byot=BYOT.ENABLE)

        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetInsertRequestBodyWithValidBody(self):
        body = json.loads(getInsertRequestBody(self.data, self.insertOptions2))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "tokens":{
                "cardNumber": "4111-1111-1111-1111",
            },
            "method": 'POST',
            "quorum": True,
            "tokenization": True
        }
        self.assertEqual(body["records"][0], expectedOutput)
    
    def testGetInsertRequestBodyWithValidBodyWithoutTokens(self):
        body = json.loads(getInsertRequestBody(self.data2, self.insertOptions))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "method": 'POST',
            "quorum": True,
            "tokenization": True
        }
        self.assertEqual(body["records"][0], expectedOutput)

    def testGetInsertRequestBodyWithValidUpsertOptions(self):
        body = json.loads(getInsertRequestBody(self.data, InsertOptions(True,[UpsertOption(table='pii_fields',column='column1')], byot=BYOT.ENABLE)))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }, 
            "tokens": {
                "cardNumber": "4111-1111-1111-1111",
            },
            "method": 'POST',
            "quorum": True,
            "tokenization": True,
            "upsert": 'column1',
        }
        self.assertEqual(body["records"][0], expectedOutput)

    def testGetInsertRequestBodyWithValidUpsertOptionsWithOutTokens(self):
        body = json.loads(getInsertRequestBody(self.data2, InsertOptions(True,[UpsertOption(table='pii_fields',column='column1')])))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }, 
            "method": 'POST',
            "quorum": True,
            "tokenization": True,
            "upsert": 'column1',
        }
        self.assertEqual(body["records"][0], expectedOutput)

    def testGetInsertRequestBodyNoRecords(self):
        invalidData = {"invalidKey": self.data["records"]}
        try:
            getInsertRequestBody(invalidData, self.insertOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetInsertRequestBodyRecordsInvalidType(self):
        invalidData = {"records": 'records'}
        try:
            getInsertRequestBody(invalidData, self.insertOptions)
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
            getInsertRequestBody(invalidData, self.insertOptions)
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
            getInsertRequestBody(invalidData, self.insertOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_FIELDS_TYPE.value % (str(type('str'))))

    def testInvalidTokensInRecord(self):
        invalidData = {"records": [{
            "table": "table",
            "fields": {
                "card_number": "4111-1111"
            },
            "tokens": "tokens"
        }
        ]}
        try:
            getInsertRequestBody(invalidData, self.insertOptions2)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_TOKENS_TYPE.value % (str(type('str'))))

    def testEmptyTokensInRecord(self):
        invalidData = {"records": [{
            "table": "table",
            "fields": {
                "card_number": "4111-1111"
            },
            "tokens": {
            }
        }
        ]}
        try:
            getInsertRequestBody(invalidData, self.insertOptions2)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_TOKENS_IN_INSERT.value)

    def testMismatchTokensInRecord(self):
        invalidData = {"records": [{
            "table": "table",
            "fields": {
                "card_number": "4111-1111"
            },
            "tokens": {
                "cvv": "123"
            }
        }
        ]}
        try:
            getInsertRequestBody(invalidData, self.insertOptions2)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.MISMATCH_OF_FIELDS_AND_TOKENS.value)

    # def testTokensInRecord(self):
    #     invalidData = {"records": [{
    #         "table": "table",
    #         "fields": {
    #             "card_number": "4111-1111"
    #         },
    #         "tokens": {
    #             "cvv": "123"
    #         }
    #     }
    #     ]}
    #     try:
    #         getInsertRequestBody(invalidData, self.insertOptions)
    #         self.fail('Should have thrown an error')
    #     except SkyflowError as e:
    #         self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
    #         self.assertEqual(
    #             e.message, SkyflowErrorMessages.MISMATCH_OF_FIELDS_AND_TOKENS.value)

    def testGetInsertRequestBodyWithTokensValidBody(self):
        body = json.loads(getInsertRequestBody(self.data, self.insertOptions2))
        expectedOutput = {
            "tableName": "pii_fields",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "tokens": {
                "cardNumber": "4111-1111-1111-1111",

            },
            "method": 'POST',
            "quorum": True,
            "tokenization": True
        }
        self.assertEqual(body["records"][0], expectedOutput)

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
            getInsertRequestBody(invalidData, self.insertOptions)
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
            getInsertRequestBody(invalidData, self.insertOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value % (
                str(type({'a': 'b'}))))

    def testGetInsertRequestBodyWithContinueOnErrorAsTrue(self):
        try:
            options = InsertOptions(tokens=True, continueOnError=True, byot=BYOT.ENABLE)
            request = getInsertRequestBody(self.data, options)
            self.assertIn('continueOnError', request)
            request = json.loads(request)
            self.assertEqual(request['continueOnError'], True)
        except SkyflowError as e:
            self.fail('Should not have thrown an error')
    
    def testGetInsertRequestBodyWithContinueOnErrorAsFalse(self):
        try:
            options = InsertOptions(tokens=True, continueOnError=False, byot=BYOT.ENABLE)
            request = getInsertRequestBody(self.data, options)
            # assert 'continueOnError' in request
            self.assertIn('continueOnError', request)
            request = json.loads(request)
            self.assertEqual(request['continueOnError'], False)
        except SkyflowError as e:
            self.fail('Should not have thrown an error')
   
    def testGetInsertRequestBodyWithoutContinueOnError(self):
        try:
            request = getInsertRequestBody(self.data, self.insertOptions2)
            # assert 'continueOnError' not in request
            self.assertNotIn('continueOnError', request)
        except SkyflowError as e:
            self.fail('Should not have thrown an error')

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
            getInsertRequestBody(invalidjson, self.insertOptions)
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
        options = InsertOptions(tokens=False)
        result, partial = convertResponse(self.mockRequest, self.mockResponse, options)
        self.assertFalse(partial)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["skyflow_id"], 123)
        self.assertEqual(result["records"][0]["table"], "pii_fields")
        self.assertNotIn("tokens", result["records"][0])

    def testConvertResponseWithTokens(self):
        options = InsertOptions(tokens=True)
        result, partial = convertResponse(self.mockRequest, self.mockResponse, options)
        self.assertFalse(partial)
        
        self.assertEqual(len(result["records"]), 1)
        self.assertNotIn("skyflow_id", result["records"][0])
        self.assertEqual(result["records"][0]["table"], "pii_fields")

        self.assertIn("fields", result["records"][0])
        self.assertEqual(result["records"][0]["fields"]["skyflow_id"], 123)

        self.assertEqual(result["records"][0]["fields"]
                         ["cardNumber"], "card_number_token")
        self.assertEqual(result["records"][0]["fields"]
                         ["cvv"], "cvv_token")
    
    def testConvertResponseWithContinueoOnErrorSuccess(self):
        options = InsertOptions(tokens=True, continueOnError=True)
        result, partial = convertResponse(self.mockRequest, self.mockResponseCOESuccess, options)
        self.assertFalse(partial)
        
        self.assertEqual(len(result["records"]), 1)
        self.assertNotIn("errors", result)
        
        self.assertNotIn("skyflow_id", result["records"][0])
        self.assertEqual(result["records"][0]["table"], "pii_fields")

        self.assertIn("fields", result["records"][0])
        self.assertEqual(result["records"][0]["fields"]["skyflow_id"], 123)
        self.assertEqual(result["records"][0]["fields"]["cardNumber"], "card_number_token")
        self.assertEqual(result["records"][0]["fields"]["cvv"], "cvv_token")
    
    def testConvertResponseWithContinueoOnErrorPartialSuccess(self):
        options = InsertOptions(tokens=True, continueOnError=True)
        partialSuccessRequest = {
            "records": [
                self.mockRequest['records'][0],
                self.mockRequest['records'][0],
            ]
        }
        result, partial = convertResponse(partialSuccessRequest, self.mockResponseCOEPartialSuccess, options)
        self.assertTrue(partial)
        
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        
        self.assertNotIn("skyflow_id", result["records"][0])
        self.assertEqual(result["records"][0]["table"], "pii_fields")

        self.assertIn("fields", result["records"][0])
        self.assertEqual(result["records"][0]["fields"]["skyflow_id"], 123)
        self.assertEqual(result["records"][0]["fields"]["cardNumber"], "card_number_token")
        self.assertEqual(result["records"][0]["fields"]["cvv"], "cvv_token")
        
        message = self.mockResponseCOEErrorObject['Body']['error'] 
        message += ' - request id: ' + self.mockResponse['requestId']
        self.assertEqual(result["errors"][0]["error"]["code"], 400)
        self.assertEqual(result["errors"][0]["error"]["description"], message)
    
    def testConvertResponseWithContinueoOnErrorFailure(self):
        options = InsertOptions(tokens=True, continueOnError=True)
        result, partial = convertResponse(self.mockRequest, self.mockResponseCOEFailure, options)
        self.assertFalse(partial)

        self.assertEqual(len(result["errors"]), 1)
        self.assertNotIn("records", result) 
        
        message = self.mockResponseCOEErrorObject['Body']['error'] 
        message += ' - request id: ' + self.mockResponse['requestId']
        self.assertEqual(result["errors"][0]["error"]["code"], 400)
        self.assertEqual(result["errors"][0]["error"]["description"], message)

    def testInsertInvalidToken(self):
        config = Configuration('id', 'url', lambda: 'invalid-token')
        try:
            Client(config).insert({'records': []})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKEN_PROVIDER_INVALID_TOKEN.value)
            
    def testGetUpsertColumn(self):
        testUpsertOptions = [UpsertOption(table='table1',column='column1'),
                         UpsertOption(table='table2',column='column2')]
        upsertValid = getUpsertColumn('table1',upsertOptions=testUpsertOptions)
        upsertInvalid = getUpsertColumn('table3',upsertOptions=testUpsertOptions)
        self.assertEqual(upsertValid,'column1')
        self.assertEqual(upsertInvalid,'')
    
    def testValidUpsertOptions(self):
        testUpsertOptions = 'upsert_string'
        try:
            validateUpsertOptions(testUpsertOptions)
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_UPSERT_OPTIONS_TYPE.value % type(testUpsertOptions) )
        try:
            validateUpsertOptions(upsertOptions=[])
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_UPSERT_OPTIONS_LIST.value)
        try:
            validateUpsertOptions(upsertOptions=[UpsertOption(table=123,column='')])
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_UPSERT_TABLE_TYPE.value % 0)
        try:
            validateUpsertOptions(upsertOptions=[UpsertOption(table='',column='')])
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_UPSERT_OPTION_TABLE.value % 0)
        try:
            validateUpsertOptions(upsertOptions=[UpsertOption(table='table1',column=1343)])
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_UPSERT_COLUMN_TYPE.value % 0)
        try:
            validateUpsertOptions(upsertOptions=[UpsertOption(table='table2',column='')])
        except SkyflowError as e:
             self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
             self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_UPSERT_OPTION_COLUMN.value % 0)

    def testInvalidByotModeTypePassed(self):
        try:
            options = InsertOptions(byot='BYOT.DISABLE')
            getInsertRequestBody(self.data, options)
            self.fail("Should have thrown an error")
        except SkyflowError as e:
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_BYOT_TYPE.value % (type(options.byot)))
            
    def testTokensPassedWithByotModeDisable(self):
        try:
            options = InsertOptions(byot=BYOT.DISABLE)
            getInsertRequestBody(self.data, options)
            self.fail("Should have thrown an error")
        except SkyflowError as e:
            self.assertEqual(e.message, SkyflowErrorMessages.TOKENS_PASSED_FOR_BYOT_DISABLE.value)

    def testTokensNotPassedWithByotModeEnable(self):
        try:
            getInsertRequestBody(self.data2, self.insertOptions2)
            self.fail("Should have thrown an error")
        except SkyflowError as e:
            self.assertEqual(e.message, SkyflowErrorMessages.NO_TOKENS_IN_INSERT.value % "ENABLE")
    
    def testTokensNotPassedWithByotModeEnableStrict(self):
        try:
            options = InsertOptions(byot=BYOT.ENABLE_STRICT)
            getInsertRequestBody(self.data2, options)
            self.fail("Should have thrown an error")
        except SkyflowError as e:
            self.assertEqual(e.message, SkyflowErrorMessages.NO_TOKENS_IN_INSERT.value % "ENABLE_STRICT")
    
    def testTokensPassedWithByotModeEnableStrict(self):
        try:
            options = InsertOptions(byot=BYOT.ENABLE_STRICT)
            getInsertRequestBody(self.data, options)
            self.fail("Should have thrown an error")
        except SkyflowError as e:
            self.assertEqual(e.message, SkyflowErrorMessages.INSUFFICIENT_TOKENS_PASSED_FOR_BYOT_ENABLE_STRICT.value)
