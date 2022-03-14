import os
import unittest
from dotenv import dotenv_values

from skyflow.ServiceAccount._token import *
from skyflow.ServiceAccount import isExpired, isValid


class TestGenerateBearerToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/ServiceAccount/data/')
        return super().setUp()

    def testIsValid(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        try:
            token, _ = generateBearerToken(credentials_path)
            self.assertEqual(True, isValid(token))
        except SkyflowError as se:
            self.fail(se.message)

    def testIsValidEmptyToken(self):
        try:
            self.assertEqual(False, isValid(''))
        except SkyflowError as se:
            self.fail('Error '+str(se.message))

    def testIsValidInvalidToken(self):
        try:
            token = 'invalid token'
            self.assertEqual(False, isValid(token))
        except SkyflowError:
            self.fail('raised exception for invalid token')

    def testIsValidTokenExpred(self):
        expiredToken = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwczovL21hbmFnZS5za3lmbG93YXBpcy5jb20iLCJjbGkiOiJrOWZkN2ZiMzcyMDI0NDhiYmViOGNkNmUyYzQ4NTdkOSIsImV4cCI6MTY0NzI1NjM3NCwiaWF0IjoxNjQ3MjU2MzE1LCJpc3MiOiJzYS1hdXRoQG1hbmFnZS5za3lmbG93YXBpcy5jb20iLCJqdGkiOiJnYTMyZWJhMGJlMzQ0YWRmYjQxMzRjN2Y2ZTIzZjllMCIsInNjcCI6WyJyb2xlOnM1OTdjNzNjYjhjOTRlMjk4YzhlZjZjNzE0M2U0OWMyIl0sInN1YiI6InRlc3Qgc3ZjIGFjYyJ9.OrkSyNtXOVtfL3JNYaArlmUFg0txJFV6o3SE_wadPwZ_h1BtMuoKPo1LOAe-4HhS16i34HcfTTiHmg2ksx5KbD_sdx1intaDWZGXs-6TPvDK8mdFrBblp3nP1y1O_PHEnCMmPD3haZVMj_9jyTKPb6R8qBbMjr-UzXAUCCTiq9XqEd81wY8FsZeKwSQFqbdFdECaPsk8m-k8s7BKc_VLtHXdYXp4vNgjgleSeX4nHHhU1w0y18q2_tPwgLG-MZ2I7pF60Owk9T7f7gSuCpVfa6zYvpYiYFjQayFmYc6tJgEuOyGD_VFKKUUW4TszeNyJOCF15dPDO2JIeGh3xDJ8PA'
        try:
            self.assertEqual(False, isValid(expiredToken))
        except SkyflowError:
            self.fail('raised error for expired token')

    def testIsExpired(self):
        env_values = dotenv_values('.env')
        credentials_path = env_values['CREDENTIALS_FILE_PATH']
        try:
            token, _ = generateBearerToken(credentials_path)
            self.assertEqual(True, isExpired(token))
        except SkyflowError as se:
            self.fail(se.message)

    def testIsExpiredInvalidToken(self):
        try:
            token = 'invalid token'
            self.assertEqual(False, isExpired(token))
        except SkyflowError as se:
            self.fail('raised exception for invalid token')

    def testIsExpiredEmptyToken(self):
        try:
            self.assertEqual(False, isExpired(''))
        except SkyflowError as se:
            self.fail('Error '+str(se.message))

    def testIsExpiredTokenExpred(self):
        expiredToken = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwczovL21hbmFnZS5za3lmbG93YXBpcy5jb20iLCJjbGkiOiJrOWZkN2ZiMzcyMDI0NDhiYmViOGNkNmUyYzQ4NTdkOSIsImV4cCI6MTY0NzI1NjM3NCwiaWF0IjoxNjQ3MjU2MzE1LCJpc3MiOiJzYS1hdXRoQG1hbmFnZS5za3lmbG93YXBpcy5jb20iLCJqdGkiOiJnYTMyZWJhMGJlMzQ0YWRmYjQxMzRjN2Y2ZTIzZjllMCIsInNjcCI6WyJyb2xlOnM1OTdjNzNjYjhjOTRlMjk4YzhlZjZjNzE0M2U0OWMyIl0sInN1YiI6InRlc3Qgc3ZjIGFjYyJ9.OrkSyNtXOVtfL3JNYaArlmUFg0txJFV6o3SE_wadPwZ_h1BtMuoKPo1LOAe-4HhS16i34HcfTTiHmg2ksx5KbD_sdx1intaDWZGXs-6TPvDK8mdFrBblp3nP1y1O_PHEnCMmPD3haZVMj_9jyTKPb6R8qBbMjr-UzXAUCCTiq9XqEd81wY8FsZeKwSQFqbdFdECaPsk8m-k8s7BKc_VLtHXdYXp4vNgjgleSeX4nHHhU1w0y18q2_tPwgLG-MZ2I7pF60Owk9T7f7gSuCpVfa6zYvpYiYFjQayFmYc6tJgEuOyGD_VFKKUUW4TszeNyJOCF15dPDO2JIeGh3xDJ8PA'
        try:
            self.assertEqual(False, isExpired(expiredToken))
        except SkyflowError:
            self.fail('raised error for expired token')
