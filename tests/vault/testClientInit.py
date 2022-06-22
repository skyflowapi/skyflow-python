'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import logging
import unittest


from skyflow.vault._config import *
from skyflow.vault._client import Client
from skyflow.errors._skyflowerrors import *
from skyflow import set_log_level, LogLevel


class TestConfig(unittest.TestCase):

    def testClientInitInvalidVaultURL(self):
        config = Configuration('VAULT ID', 22, lambda: 'token')

        try:
            client = Client(config)
            self.fail('Should fail due to invalid VAULT URL')
        except SkyflowError as e:
            self.assertEqual(SkyflowErrorCodes.INVALID_INPUT.value, e.code)
            self.assertEqual(
                SkyflowErrorMessages.VAULT_URL_INVALID_TYPE.value % (type(22)), e.message)

    def testClientInitInvalidTokenProvider(self):
        config = Configuration('VAULT ID', 'VAULT URL', 'token')

        try:
            client = Client(config)
            self.fail('Should fail due to invalid TOKEN PROVIDER')
        except SkyflowError as e:
            self.assertEqual(SkyflowErrorCodes.INVALID_INPUT.value, e.code)
            self.assertEqual(SkyflowErrorMessages.TOKEN_PROVIDER_ERROR.value % (
                type('token')), e.message)

    def testLogLevel(self):
        skyflowLogger = logging.getLogger('skyflow')
        self.assertEqual(skyflowLogger.getEffectiveLevel(), logging.ERROR)
        set_log_level(logLevel=LogLevel.DEBUG)
        self.assertEqual(skyflowLogger.level, logging.DEBUG)
