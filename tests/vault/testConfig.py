import unittest

from skyflow.vault._config import *

class TestConfig(unittest.TestCase):
    def testInsertOptions(self):
        defaultOptions = InsertOptions()
        noTokensOption = InsertOptions(tokens=False)

        self.assertEqual(defaultOptions.tokens, True)
        self.assertEqual(noTokensOption.tokens, False)

    def testSkyflowConfig(self):
        myconfig = Configuration("vaultID", "https://vaults.skyflow.com", lambda: "token")
        self.assertEqual(myconfig.vaultID, "vaultID")
        self.assertEqual(myconfig.vaultURL, "https://vaults.skyflow.com")
        self.assertEqual(myconfig.tokenProvider(), "token")

    def testConnectionConfigDefaults(self):
        config = ConnectionConfig('https://skyflow.com', methodName=RequestMethod.GET)
        self.assertEqual(config.connectionURL, 'https://skyflow.com')
        self.assertEqual(config.methodName, RequestMethod.GET)
        self.assertDictEqual(config.pathParams, {})
        self.assertDictEqual(config.queryParams, {})
        self.assertDictEqual(config.requestHeader, {})
        self.assertDictEqual(config.requestBody, {})
        
    def testConfigArgs(self):
        configOnlyTokenProvider = Configuration(lambda: "token")
        self.assertIsNotNone(configOnlyTokenProvider.tokenProvider)
        self.assertEqual(configOnlyTokenProvider.vaultID, '')
        self.assertEqual(configOnlyTokenProvider.vaultURL, '')
        
        try:
            Configuration()
        except TypeError as e:
            self.assertEqual(e.args[0], "tokenProvider must be given")

