import unittest

from skyflow.ServiceAccount._token import GenerateToken
from skyflow.Vault._gateway import *
from skyflow.Vault._client import *
from skyflow.Vault._config import *
from skyflow.Errors._skyflowErrors import *
from dotenv import dotenv_values

class testGateway(unittest.TestCase):
    def testCreateRequestDefault(self):
        config = GatewayConfig('https://skyflow.com/', RequestMethod.GET)
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
        config = GatewayConfig('https://skyflow.com/', RequestMethod.GET, requestBody=invalidJsonBody)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_REQUEST_BODY.value)

    def testCreateRequestInvalidBodyType(self):
        nonDictBody = 'body'
        config = GatewayConfig('https://skyflow.com/', RequestMethod.GET, requestBody=nonDictBody)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_REQUEST_BODY.value)

    def testCreateRequestBodyInvalidHeadersJson(self):
        invalidJsonHeaders = {'somekey': unittest}
        config = GatewayConfig('https://skyflow.com/', RequestMethod.GET, requestHeader=invalidJsonHeaders)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_HEADERS.value)

    
    def testCreateRequestBodyHeadersNotDict(self):
        invalidJsonHeaders = 'invalidheaderstype'
        config = GatewayConfig('https://skyflow.com/', RequestMethod.GET, requestHeader=invalidJsonHeaders)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_HEADERS.value)

    def testCreateRequestInvalidURL(self):
        invalidUrl = 'https::///skyflow.com'
        config = GatewayConfig(invalidUrl, RequestMethod.GET)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_URL.value%(invalidUrl))


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
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value%(str(type('department')), str(type(['str']))))
    def testVerifyParamsQueryParamsNotDict(self):
        queryParams = {'name': 'john', 2: [json], 'action': 1}
        try:
            verifyParams(queryParams, {})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_QUERY_PARAM_TYPE.value%(str(type(2)), str(type(['str']))))
    
    def testVerifyParamsInvalidPathParams(self):
        pathParams = 'string'
        try:
            verifyParams({}, pathParams)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_PATH_PARAMS.value)
    def testVerifyParamsInvalidQueryParams(self):
        queryParams = 'string'
        try:
            verifyParams(queryParams, {})
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_QUERY_PARAMS.value)

    def testInvokeGatewayCvvGenSuccess(self):
        env_values = dotenv_values('.env')
        gatewayUrl = env_values['CVV_GEN_GATEWAY_URL']

        def tokenProvider():
            token, _ = GenerateToken(env_values['CREDENTIALS_FILE_PATH'])
            return token

        config = Configuration(env_values['VAULT_ID'], env_values['VAULT_URL'], tokenProvider)
        gatewayConfig = GatewayConfig(gatewayUrl, RequestMethod.POST,
        requestHeader={
                    'Content-Type': 'application/json',
                    'Authorization': env_values['VISA_GATEWAY_BASIC_AUTH']
        },
        requestBody=
        {
            "expirationDate": {
                "mm": "12",
                "yy": "22"
            }
        },
        pathParams={'cardID': env_values['DETOKENIZE_TEST_TOKEN']})
        client = Client(config)


        try:
            resp = client.invokeGateway(gatewayConfig)
            self.assertIsNotNone(resp['resource']['cvv2'])
            self.assertIsNotNone(resp['processingTimeinMs'])
            self.assertIsNotNone(resp['receivedTimestamp'])
        except SkyflowError as e:
            print(e)
            self.fail()