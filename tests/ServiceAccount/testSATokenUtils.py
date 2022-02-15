import os
import unittest

from skyflow.ServiceAccount._token import *


class TestGenerateBearerToken(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/ServiceAccount/data/')
        return super().setUp()

    def testGetSetGo(self):
        return
 