import unittest
from skyflow.Vault._token import tokenProviderWrapper
from skyflow.ServiceAccount import generateBearerToken
from skyflow.Errors._skyflowErrors import *

class TestTokenProviderWrapper(unittest.TestCase):

    def testInvalidStoredToken(self):
        newerToken = ''
        def tokenProvider():
            newerToken = generateBearerToken('credentials.json')
            return newerToken

        try:
            newToken = tokenProviderWrapper('invalid', tokenProvider, "Test")
            self.fail('Should have thrown invalid jwt error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.JWT_DECODE_ERROR.value)
         
    def testNoStoredToken(self):
        self.newToken = ''
        def tokenProvider():
            self.newerToken, _ = generateBearerToken('credentials.json')
            return self.newToken

        try:
            newerToken = tokenProviderWrapper('', tokenProvider, "Test")
            self.assertEqual(newerToken, self.newToken)
        except SkyflowError:
            self.fail('Should have decoded token')
            

    def testStoredTokenNotExpired(self):
        self.newerToken = ''
        def tokenProvider():
            self.newerToken, _ = generateBearerToken('credentials.json')
            return self.newerToken

        try:
            newToken = tokenProviderWrapper(tokenProvider(), tokenProvider, "Test")
            self.assertEqual(newToken, self.newerToken)
        except SkyflowError:
            self.fail('Should have decoded token')