import unittest

from skyflow.Vault._config import *
from skyflow.Vault._client import Client
from skyflow.Errors._skyflowErrors import *

class TestConfig(unittest.TestCase):
    def testClientInitInvalidVaultID(self):
        config = SkyflowConfiguration(None, 'VAULT URL', lambda: 'token')

        try:
            client = Client(config)
            self.fail('Should fail due to invalid VAULT ID')
        except SkyflowError as e:
            self.assertEqual(SkyflowErrorCodes.INVALID_INPUT.value, e.code)
            self.assertEqual(SkyflowErrorMessages.VAULT_ID_INVALID_TYPE.value%(type(None)), e.message)

    
    def testClientInitInvalidVaultURL(self):
        config = SkyflowConfiguration('VAULT ID', 22, lambda: 'token')

        try:
            client = Client(config)
            self.fail('Should fail due to invalid VAULT URL')
        except SkyflowError as e:
            self.assertEqual(SkyflowErrorCodes.INVALID_INPUT.value, e.code)
            self.assertEqual(SkyflowErrorMessages.VAULT_URL_INVALID_TYPE.value%(type(22)), e.message)

    
    def testClientInitInvalidTokenProvider(self):
        config = SkyflowConfiguration('VAULT ID', 'VAULT URL', 'token')

        try:
            client = Client(config)
            self.fail('Should fail due to invalid TOKEN PROVIDER')
        except SkyflowError as e:
            self.assertEqual(SkyflowErrorCodes.INVALID_INPUT.value, e.code)
            self.assertEqual(SkyflowErrorMessages.TOKEN_PROVIDER_ERROR.value%(type('token')), e.message)