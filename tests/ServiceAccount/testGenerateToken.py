import unittest
import os
from dotenv import dotenv_values
from skyflow.ServiceAccount import GenerateBearerToken
from skyflow.Errors._skyflowErrors import *

class TestGenerateBearerToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/ServiceAccount/data/')
        return super().setUp()
    
    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testWithInvalidFilePath(self):
        try:
            GenerateBearerToken('unknownfilepath')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % ('unknownfilepath'))
    

    def testInvalidJSON(self):
        path = self.getDataPath('empty')
        try:
            GenerateBearerToken(path)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % (path))

    def testWithNoPrivateKey(self):
        try:
            GenerateBearerToken(self.getDataPath('noPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)
    
    def testWithNoClientID(self):
        try:
            GenerateBearerToken(self.getDataPath('noClientID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_CLIENT_ID.value)

    def testWithNoKeyID(self):
        try:
            GenerateBearerToken(self.getDataPath('noKeyID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_KEY_ID.value)

    def testWithNoTokenURI(self):
        try:
            GenerateBearerToken(self.getDataPath('noTokenURI'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_TOKEN_URI.value)

    def testInvalidCreds(self):
        try:
             GenerateBearerToken(self.getDataPath('invalidPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.JWT_INVALID_FORMAT.value)

    def testGenerateBearerTokenSuccess(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        try:
            token, type = GenerateBearerToken(credentials_path)
            self.assertIsNotNone(token)
            self.assertEqual(type, 'Bearer')
        except SkyflowError:
            self.fail('Should have successfully returned the token')

