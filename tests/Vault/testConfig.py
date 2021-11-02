import unittest

from skyflow.Vault._config import *

class TestConfig(unittest.TestCase):
    def testInsertOptions(self):
        defaultOptions = InsertOptions()
        noTokensOption = InsertOptions(tokens=False)

        self.assertEqual(defaultOptions.tokens, True)
        self.assertEqual(noTokensOption.tokens, False)

    def testSkyflowConfig(self):
        myconfig = SkyflowConfiguration("vaultID", "https://vaults.skyflow.com", lambda: "token")
        self.assertEqual(myconfig.vaultID, "vaultID")
        self.assertEqual(myconfig.vaultURL, "https://vaults.skyflow.com")
        self.assertEqual(myconfig.tokenProvider(), "token")

    def testGatewayConfigDefaults(self):
        gatewayConfig = GatewayConfig('https://skyflow.com', methodName=RequestMethod.GET)
        self.assertEqual(gatewayConfig.gatewayURL, 'https://skyflow.com')
        self.assertEqual(gatewayConfig.methodName, RequestMethod.GET)
        self.assertDictEqual(gatewayConfig.pathParams, {})
        self.assertDictEqual(gatewayConfig.queryParams, {})
        self.assertDictEqual(gatewayConfig.requestHeader, {})
        self.assertDictEqual(gatewayConfig.requestBody, {})
        self.assertDictEqual(gatewayConfig.responseBody, {})