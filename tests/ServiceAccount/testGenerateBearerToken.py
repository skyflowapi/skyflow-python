import unittest
import os
from dotenv import dotenv_values
from skyflow.ServiceAccount import generateBearerToken, generateBearerTokenFromCreds, GenerateToken
from skyflow.Errors._skyflowErrors import *
import json
from skyflow.ServiceAccount._token import getSignedJWT, getResponseToken, sendRequestWithToken


class TestGenerateBearerToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/ServiceAccount/data/')
        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testWithInvalidFilePath(self):
        try:
            generateBearerToken('unknownfilepath')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % ('unknownfilepath'))

    def testInvalidJSON(self):
        path = self.getDataPath('empty')
        try:
            generateBearerToken(path)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % (path))

    def testWithNoPrivateKey(self):
        try:
            generateBearerToken(self.getDataPath('noPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)

    def testWithNoClientID(self):
        try:
            generateBearerToken(self.getDataPath('noClientID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_CLIENT_ID.value)

    def testWithNoKeyID(self):
        try:
            generateBearerToken(self.getDataPath('noKeyID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_KEY_ID.value)

    def testWithNoTokenURI(self):
        try:
            generateBearerToken(self.getDataPath('noTokenURI'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_TOKEN_URI.value)

    def testInvalidCreds(self):
        try:
            generateBearerToken(self.getDataPath('invalidPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.JWT_INVALID_FORMAT.value)

    def testgenerateBearerTokenSuccess(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        try:
            token, type = generateBearerToken(credentials_path)
            self.assertIsNotNone(token)
            self.assertEqual(type, 'Bearer')
        except SkyflowError:
            self.fail('Should have successfully returned the token')

    def testGenerateBearerTokenFromCredsInvalid(self):
        creds_file = open(self.getDataPath('invalidPrivateKey'), 'r')
        credentialsString = json.dumps(creds_file.read())
        creds_file.close()
        try:
            generateBearerTokenFromCreds(credentialsString)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)

    def testGenerateBearerTokenFromCredsFail(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        creds_file = open(credentials_path, 'r')
        credentialsString = json.dumps(creds_file.read())
        try:
            generateBearerTokenFromCreds(credentialsString)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)

    def testGenerateBearerTokenFromCredsSuccess(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        creds_file = open(credentials_path, 'r')
        credentialsString = json.dumps(
            json.loads(creds_file.read()))
        creds_file.close()
        try:
            token, type = generateBearerTokenFromCreds(credentialsString)
            self.assertIsNotNone(token)
            self.assertEqual(type, "Bearer")
        except SkyflowError as se:
            self.fail()

    def testNonExistentFileArg(self):
        try:
            generateBearerToken('non-existent-file.json')
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % 'non-existent-file.json')

    def testInvalidJSONInCreds(self):
        filepath = self.getDataPath('invalidJson')
        try:
            generateBearerToken(filepath)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % filepath)
        try:
            generateBearerTokenFromCreds(self.getDataPath('invalid-json'))
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_CREDENTIALS.value)

    def testGenerateToken(self):
        try:
            GenerateToken(self.getDataPath('invalid-json'))
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)

    def testGetSignedJWTInvalidValue(self):
        try:
            getSignedJWT('{}clientID', 'keyId',
                         'privateKey', 'ww.tokenURI.com')
            self.fail('invalid jwt signed')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.JWT_INVALID_FORMAT.value)

    def testGetResponseTokenNoType(self):
        try:
            getResponseToken({'accessToken': 'only access token'})
            self.fail('Should throw')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.SERVER_ERROR.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_TOKEN_TYPE.value)

    def testGetResponseTokenNoType(self):
        try:
            getResponseToken({'tokenType': 'only token type'})
            self.fail('Should throw')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.SERVER_ERROR.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_ACCESS_TOKEN.value)

    def testSendRequestInvalidUrl(self):
        try:
            sendRequestWithToken('invalidurl', 'invalid-token')
            self.fail('Not throwing on invalid url')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.INVALID_URL.value % 'invalidurl')
