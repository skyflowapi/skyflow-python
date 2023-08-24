'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import json
import unittest
import os
from unittest import mock
import requests
from requests.models import Response
from skyflow.vault._query import getQueryRequestBody, getQueryResponse
from skyflow.errors._skyflow_errors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.vault._client import Client
from skyflow.vault._config import Configuration, QueryOptions

class TestQuery(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/vault/data/')
        query = "SELECT * FROM pii_fields WHERE skyflow_id='3ea3861-x107-40w8-la98-106sp08ea83f'"
        self.data = {"query": query}
        self.mockRequest = {"records": [query]}

        self.mockResponse = {
            "records": [
                {
                "fields": {
                        "card_number": "XXXXXXXXXXXX1111",
                        "card_pin": "*REDACTED*",
                        "cvv": "",
                        "expiration_date": "*REDACTED*",
                        "expiration_month": "*REDACTED*",
                        "expiration_year": "*REDACTED*",
                        "name": "a***te",
                        "skyflow_id": "3ea3861-x107-40w8-la98-106sp08ea83f",
                        "ssn": "XXX-XX-6789",
                        "zip_code": None
                    },
                "tokens": None
                }
            ]
        }
        
        self.requestId = '5d5d7e21-c789-9fcc-ba31-2a279d3a28ef'
        
        self.mockApiError = {
            "error": {
                "grpc_code": 13,
                "http_code": 500,
                "message": "ERROR (internal_error): Could not find Notebook Mapping Notebook Name was not found",
                "http_status": "Internal Server Error",
                "details": []
            }
        }
        
        self.mockFailResponse = {
            "error": {
                "code": 500,
                "description": "ERROR (internal_error): Could not find Notebook Mapping Notebook Name was not found - request id: 5d5d7e21-c789-9fcc-ba31-2a279d3a28ef"
            }
        }
        
        self.queryOptions = QueryOptions()

        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetQueryRequestBodyWithValidBody(self):
        body = json.loads(getQueryRequestBody(self.data, self.queryOptions))
        expectedOutput = {
            "query": "SELECT * FROM pii_fields WHERE skyflow_id='3ea3861-x107-40w8-la98-106sp08ea83f'",
        }
        self.assertEqual(body, expectedOutput)
    
    def testGetQueryRequestBodyNoQuery(self):
        invalidData = {"invalidKey": self.data["query"]}
        try:
            getQueryRequestBody(invalidData, self.queryOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.QUERY_KEY_ERROR.value)

    def testGetQueryRequestBodyInvalidType(self):
        invalidData = {"query": ['SELECT * FROM table_name']}
        try:
            getQueryRequestBody(invalidData, self.queryOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_QUERY_TYPE.value % (str(type(invalidData["query"]))))
    
    def testGetQueryRequestBodyEmptyBody(self):
        invalidData = {"query": ''}
        try:
            getQueryRequestBody(invalidData, self.queryOptions)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_QUERY.value)

    def testGetQueryValidResponse(self):
        response = Response()
        response.status_code = 200
        response._content = b'{"key": "value"}'
        try:
            responseDict = getQueryResponse(response)
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

    def testGetQueryResponseSuccessInvalidJson(self):
        invalid_response = Response()
        invalid_response.status_code = 200
        invalid_response._content = b'invalid-json'
        try:
            getQueryResponse(invalid_response)
            self.fail('not failing on invalid json')
        except SkyflowError as se:
            self.assertEqual(se.code, 200)
            self.assertEqual(
                se.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % 'invalid-json')
            
    def testGetQueryResponseFailInvalidJson(self):
        invalid_response = mock.Mock(
            spec=requests.Response,
            status_code=404,
            content=b'error'
        )
        invalid_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not found")
        try:
            getQueryResponse(invalid_response)
            self.fail('Not failing on invalid error json')
        except SkyflowError as se:
            self.assertEqual(se.code, 404)
            self.assertEqual(
                se.message, SkyflowErrorMessages.RESPONSE_NOT_JSON.value % 'error')
   
    def testGetQueryResponseFail(self):
        response = mock.Mock(
            spec=requests.Response,
            status_code=500,
            content=json.dumps(self.mockApiError).encode('utf-8')
        )
        response.headers = {"x-request-id": self.requestId}
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        try:
            getQueryResponse(response)
            self.fail('not throwing exception when error code is 500')
        except SkyflowError as e:
            self.assertEqual(e.code, 500)
            self.assertEqual(e.message,  SkyflowErrorMessages.SERVER_ERROR.value)
            self.assertDictEqual(e.data,  self.mockFailResponse)

    def testQueryInvalidToken(self):
        config = Configuration('id', 'url', lambda: 'invalid-token')
        try:
            Client(config).query({'query': 'SELECT * FROM table_name'})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKEN_PROVIDER_INVALID_TOKEN.value)
