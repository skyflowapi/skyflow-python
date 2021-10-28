import unittest
import os
from skyflow.Vault._insert import getInsertRequestBody
from skyflow.Vault._client import Client
from skyflow.ServiceAccount import GenerateToken

class TestInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.dataPath = os.path.join(os.getcwd(), 'tests/Vault/data/')
        field = {
            "table": "persons",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            }
        }
        self.data = {"records": [field]}
        return super().setUp()


    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetInsertRequestBodyWithValidBody(self):
        body = getInsertRequestBody(self.data)
        expectedOutput = {
            "tableName": "persons",
            "fields": {
                "cardNumber": "4111-1111-1111-1111",
                "cvv": "234"
            },
            "method": 'POST',
            "quorum": True
        }
        self.assertEqual(body["records"][0], expectedOutput)

    def testClientInsert(self):
        def tokenProvider():
            token, type = GenerateToken(self.getDataPath('credentials'))
            return token
        client = Client('bdc271aee8584eed88253877019657b3', 'https://sb.area51.vault.skyflowapis.dev', tokenProvider)

        data = {
            "records": [
                {
                    "table": "persons",
                    "fields": {
                        "cvv": "122",
                        "card_expiration": "1221",
                        "card_number": "4111111111111111",
                        "name": {"first_name": "Bob"}
                    }
                }
            ]
        }
        print("===================>", client.insert(data).content)

