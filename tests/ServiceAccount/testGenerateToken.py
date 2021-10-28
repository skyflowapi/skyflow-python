import unittest
import os
import sys
from skyflow.ServiceAccount import GenerateToken
from skyflow.Errors._skyflowErrors import *

class TestGenerateToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/ServiceAccount/data/')
        return super().setUp()
    
    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testWithInvalidFilePath(self):
        try:
            GenerateToken('unknownfilepath')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % ('unknownfilepath'))
    

    def testInvalidJSON(self):
        path = self.getDataPath('empty')
        try:
            GenerateToken(path)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % (path))

    def testWithNoPrivateKey(self):
        try:
            GenerateToken(self.getDataPath('noPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)
    
    def testWithNoClientID(self):
        try:
            GenerateToken(self.getDataPath('noClientID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_CLIENT_ID.value)

    def testWithNoKeyID(self):
        try:
            GenerateToken(self.getDataPath('noKeyID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_KEY_ID.value)

    def testWithNoTokenURI(self):
        try:
            GenerateToken(self.getDataPath('noTokenURI'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.MISSING_TOKEN_URI.value)

    def testInvalidCreds(self):
        try:
             GenerateToken(self.getDataPath('invalidPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(se.message, SkyflowErrorMessages.JWT_INVALID_FORMAT.value)

