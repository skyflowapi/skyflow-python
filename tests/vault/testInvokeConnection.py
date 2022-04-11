import unittest

from requests import request
from skyflow.service_account._token import generate_bearer_token
from skyflow.vault._connection import *
from skyflow.vault._client import *
from skyflow.vault._config import *
from skyflow.errors._skyflowerrors import *
from dotenv import dotenv_values


class testInvokeConnection(unittest.TestCase):
    def testCreateRequestDefault(self):
        config = ConnectionConfig('https://skyflow.com/', RequestMethod.GET)
        try:
            req = createRequest(config)
            body, url, method = req.body, req.url, req.method
            self.assertEqual(url, 'https://skyflow.com/')
            self.assertEqual(body, '{}')
            self.assertEqual(method, RequestMethod.GET.value)
        except SkyflowError:
            self.fail()

    def testCreateRequestInvalidJSONBody(self):
        invalidJsonBody = {'somekey': unittest}
        config = ConnectionConfig(
            'https://skyflow.com/', RequestMethod.GET, requestBody=invalidJsonBody)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_REQUEST_BODY.value)

    def testCreateRequestInvalidBodyType(self):
        nonDictBody = 'body'
        config = ConnectionConfig(
            'https://skyflow.com/', RequestMethod.GET, requestBody=nonDictBody)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_REQUEST_BODY.value)

    def testCreateRequestBodyInvalidHeadersJson(self):
        invalidJsonHeaders = {'somekey': unittest}
        config = ConnectionConfig(
            'https://skyflow.com/', RequestMethod.GET, requestHeader=invalidJsonHeaders)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_HEADERS.value)

    def testCreateRequestBodyHeadersNotDict(self):
        invalidJsonHeaders = 'invalidheaderstype'
        config = ConnectionConfig(
            'https://skyflow.com/', RequestMethod.GET, requestHeader=invalidJsonHeaders)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_HEADERS.value)

    def testCreateRequestInvalidURL(self):
        invalidUrl = 'https::///skyflow.com'
        config = ConnectionConfig(invalidUrl, RequestMethod.GET)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_URL.value % (invalidUrl))

    def testPathParams(self):
        try:
            url = parsePathParams(url='https://skyflow.com/{name}/{department}/content/{action}',
                                  pathParams={'name': 'john', 'department': 'test', 'action': 'download'})

            expectedURL = 'https://skyflow.com/john/test/content/download'

            self.assertEqual(url, expectedURL)
        except SkyflowError as e:
            self.fail()

    def testVerifyParamsPathParamsNotDict(self):
        pathParams = {'name': 'john', 'department': ['test'], 'action': 1}
        try:
            verifyParams({}, pathParams)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value % (
                str(type('department')), str(type(['str']))))

    def testVerifyParamsQueryParamsNotDict(self):
        queryParams = {'name': 'john', 2: [json], 'action': 1}
        try:
            verifyParams(queryParams, {})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_QUERY_PARAM_TYPE.value % (
                str(type(2)), str(type(['str']))))

    def testVerifyParamsInvalidPathParams(self):
        pathParams = 'string'
        try:
            verifyParams({}, pathParams)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_PATH_PARAMS.value)

    def testVerifyParamsInvalidQueryParams(self):
        queryParams = 'string'
        try:
            verifyParams(queryParams, {})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_QUERY_PARAMS.value)

    def testInvokeConnectionFailure(self):
        config = Configuration('', '', lambda: 'token')
        client = Client(config)
        connectionConfig = ConnectionConfig(
            'url', RequestMethod.POST, requestBody=[])
        try:
            client.invoke_connection(connectionConfig)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.TOKEN_PROVIDER_INVALID_TOKEN.value)
