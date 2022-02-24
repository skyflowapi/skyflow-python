import os
import unittest
from dotenv import dotenv_values

from skyflow.ServiceAccount._token import *
from skyflow.ServiceAccount import isValid

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
