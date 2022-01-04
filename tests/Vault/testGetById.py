import unittest
import os
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from skyflow.Vault import Client, Configuration, RedactionType
from skyflow.ServiceAccount import GenerateBearerToken
from dotenv import dotenv_values
import warnings

class TestGetById(unittest.TestCase):

    def setUp(self) -> None:
        self.envValues = dotenv_values(".env")
        self.dataPath = os.path.join(os.getcwd(), 'tests/Vault/data/')
        def tokenProvider():
            token, type = GenerateBearerToken(self.envValues["CREDENTIALS_FILE_PATH"])
            return token

        config = Configuration(self.envValues["VAULT_ID"], self.envValues["VAULT_URL"], tokenProvider)
        self.client = Client(config)
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        return super().setUp()

    def getDataPath(self, file):
        return self.dataPath + file + '.json'

    def testGetByIdNoRecords(self):
        invalidData = {"invalidKey": "invalid"}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.RECORDS_KEY_ERROR.value)

    def testGetByIdRecordsInvalidType(self):
        invalidData = {"records": "invalid"}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_RECORDS_TYPE.value%(str))
    
    def testGetByIdNoIds(self):
        invalidData = {"records": [{"invalid": "invalid", "table": "persons", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.IDS_KEY_ERROR.value)

    def testGetByIdInvalidIdsType(self):
        invalidData = {"records": [{"ids": "invalid", "table": "persons", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_IDS_TYPE.value%(str))

    def testGetByIdInvalidIdsType2(self):
        invalidData = {"records": [{"ids": ["123", 123], "table": "persons", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_ID_TYPE.value%(int))

    def testGetByIdNoTable(self):
        invalidData = {"records": [{"ids": ["id1", "id2"], "invalid": "invalid", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.TABLE_KEY_ERROR.value)

    def testGetByIdInvalidTableType(self):
        invalidData = {"records": [{"ids": ["id1", "id2"], "table": ["invalid"], "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_TABLE_TYPE.value%(list))

    def testGetByIdNoRedaction(self):
        invalidData = {"records": [{"ids": ["id1", "id2"], "table": "persons", "invalid": "invalid"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.REDACTION_KEY_ERROR.value)

    def testGetByIdInvalidRedactionType(self):
        invalidData = {"records": [{"ids": ["id1", "id2"], "table": "persons", "redaction": "PLAIN_TEXT"}]}
        try:
            self.client.getById(invalidData)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.INVALID_INPUT.value)
            self.assertEqual(e.message, SkyflowErrorMessages.INVALID_REDACTION_TYPE.value%(str))

    def testGetByIdSuccess(self):
        data = { "records": [
            {
                "ids": [self.envValues["SKYFLOW_ID1"], self.envValues["SKYFLOW_ID2"], self.envValues["SKYFLOW_ID3"]],
                "table": "persons",
                "redaction": RedactionType.PLAIN_TEXT
            }
        ]}
        try:
            response = self.client.getById(data)
            self.assertIsNotNone(response["records"][0]["fields"])
            self.assertIsNotNone(response["records"][0]["fields"]["skyflow_id"])
            self.assertEqual(response["records"][0]["table"], "persons")
            self.assertIsNotNone(response["records"][1]["fields"])
            self.assertIsNotNone(response["records"][1]["fields"]["skyflow_id"])
            self.assertEqual(response["records"][1]["table"], "persons")
        except SkyflowError as e:
            self.fail('Should not throw an error')

    def testDetokenizePartialSuccess(self):
        data = { "records": [
            {
                "ids": [self.envValues["SKYFLOW_ID1"], self.envValues["SKYFLOW_ID2"], self.envValues["SKYFLOW_ID3"]],
                "table": "persons",
                "redaction": RedactionType.PLAIN_TEXT
            },
            {
            "ids": [self.envValues["SKYFLOW_ID3"]],
            "table": "persons",
            "redaction": RedactionType.PLAIN_TEXT
        }]}
        try:
            self.client.getById(data)
            self.fail('Should have thrown an error')
        except SkyflowError as e:
            self.assertEqual(e.code, SkyflowErrorCodes.PARTIAL_SUCCESS.value)
            self.assertEqual(e.message, SkyflowErrorMessages.PARTIAL_SUCCESS.value)
            self.assertIsNotNone(e.data["records"][0]["fields"])
            self.assertIsNotNone(e.data["records"][0]["fields"]["skyflow_id"])
            self.assertEqual(e.data["records"][0]["table"], "persons")
            self.assertIsNotNone(e.data["records"][1]["fields"]["skyflow_id"])
            self.assertIsNotNone(e.data["records"][1]["fields"])
            self.assertEqual(e.data["records"][1]["table"], "persons")
            self.assertEqual(e.data["errors"][0]["error"]["code"], 404)
            self.assertEqual(e.data["errors"][0]["error"]["description"], "No Records Found")

