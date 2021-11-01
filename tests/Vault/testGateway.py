import unittest

from skyflow.Vault._gateway import *
from skyflow.Vault._config import GatewayConfig, RequestMethod
from skyflow.Errors._skyflowErrors import *

class testGateway(unittest.TestCase):
    def testCreateRequestDefault(self):
        config = GatewayConfig('https://skyflow.com', RequestMethod.GET)
        try:
            createRequest(config)
        except SkyflowError:
            self.fail()

    def testCreateRequestInvalidURL(self):
        invalidUrl = 'https::///skyflow.com'
        config = GatewayConfig(invalidUrl, RequestMethod.GET)
        try:
            createRequest(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_URL.value%(invalidUrl))

    def testPathParamsHappyPath(self):
        try:
            url = parsePathParams(url='https://skyflow.com/{name}/{department}/content/{action}', 
            pathParams={'name': 'john', 'department': 'test', 'action': 'download'})

            expectedURL = 'https://skyflow.com/john/test/content/download'

            self.assertEqual(url, expectedURL)
        except SkyflowError as e:
            print(e)
            self.fail()

    def testPathParamsInvalidParams(self):
        url = 'https://skyflow.com/{name}/{department}/content/{action}'
        params = {'name': 'john', 'department': ['test'], 'action': 1}
        try:
            parsePathParams(url, params)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_PATH_PARAM_TYPE.value%(str(type('name')), str(type(['str']))))