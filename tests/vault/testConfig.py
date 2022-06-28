'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from http import client
import unittest

from skyflow.vault._config import *
from skyflow.vault import Client
from skyflow.errors._skyflowerrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages


class TestConfig(unittest.TestCase):
    def testInsertOptions(self):
        defaultOptions = InsertOptions()
        noTokensOption = InsertOptions(tokens=False)

        self.assertEqual(defaultOptions.tokens, True)
        self.assertEqual(noTokensOption.tokens, False)

    def testSkyflowConfig(self):
        myconfig = Configuration(
            "vaultID", "https://vaults.skyflow.com", lambda: "token")
        self.assertEqual(myconfig.vaultID, "vaultID")
        self.assertEqual(myconfig.vaultURL, "https://vaults.skyflow.com")
        self.assertEqual(myconfig.tokenProvider(), "token")

    def testConnectionConfigDefaults(self):
        config = ConnectionConfig(
            'https://skyflow.com', methodName=RequestMethod.GET)
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

    def testConfigInvalidIdType(self):
        try:
            config = Configuration(
                ['invalid'], 'www.example.org', lambda: 'token')
            Client(config)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.VAULT_ID_INVALID_TYPE.value % type(['invalid']))

    def testCheckConfigEmptyVaultId(self):
        try:
            config = Configuration('', '', lambda: 'token')
            Client(config)._checkConfig('test')
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_VAULT_ID.value)

    def testCheckConfigEmptyVaultURL(self):
        try:
            config = Configuration('vault_id', '', lambda: 'token')
            Client(config)._checkConfig('test')
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.EMPTY_VAULT_URL.value)
