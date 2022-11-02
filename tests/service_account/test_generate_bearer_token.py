'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import unittest
import os
from dotenv import dotenv_values
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, generate_bearer_token
from skyflow.errors._skyflow_errors import *
import json
from skyflow.service_account._token import getSignedJWT, getResponseToken, sendRequestWithToken


class TestGenerateBearerToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(
            os.getcwd(), 'tests/service_account/data/')
        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testWithInvalidFilePath(self):
        try:
            generate_bearer_token('unknownfilepath')
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % ('unknownfilepath'))

    def testInvalidJSON(self):
        path = self.getDataPath('empty')
        try:
            generate_bearer_token(path)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % (path))

    def testWithNoPrivateKey(self):
        try:
            generate_bearer_token(self.getDataPath('noPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)

    def testWithNoClientID(self):
        try:
            generate_bearer_token(self.getDataPath('noClientID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_CLIENT_ID.value)

    def testWithNoKeyID(self):
        try:
            generate_bearer_token(self.getDataPath('noKeyID'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_KEY_ID.value)

    def testWithNoTokenURI(self):
        try:
            generate_bearer_token(self.getDataPath('noTokenURI'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_TOKEN_URI.value)

    def testInvalidCreds(self):
        try:
            generate_bearer_token(self.getDataPath('invalidPrivateKey'))
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.JWT_INVALID_FORMAT.value)

    def testGenerateBearerTokenFromCredsInvalid(self):
        creds_file = open(self.getDataPath('invalidPrivateKey'), 'r')
        credentialsString = json.dumps(creds_file.read())
        creds_file.close()
        try:
            generate_bearer_token_from_creds(credentialsString)
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
            generate_bearer_token_from_creds(credentialsString)
        except SkyflowError as se:
            self.assertEqual(se.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                se.message, SkyflowErrorMessages.MISSING_PRIVATE_KEY.value)

    def testNonExistentFileArg(self):
        try:
            generate_bearer_token('non-existent-file.json')
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FILE_NOT_FOUND.value % 'non-existent-file.json')

    def testInvalidJSONInCreds(self):
        filepath = self.getDataPath('invalidJson')
        try:
            generate_bearer_token(filepath)
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.FILE_INVALID_JSON.value % filepath)
        try:
            generate_bearer_token_from_creds(self.getDataPath('invalid-json'))
            self.fail()
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(
                e.message, SkyflowErrorMessages.INVALID_CREDENTIALS.value)

    def testGenerateToken(self):
        try:
            generate_bearer_token(self.getDataPath('invalid-json'))
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

    def testGetResponseTokenNoAccessToken(self):
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
