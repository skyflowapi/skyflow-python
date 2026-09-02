import unittest
from skyflow.vault.connection._invoke_connection_response import InvokeConnectionResponse


class TestInvokeConnectionResponse(unittest.TestCase):
    def test_repr(self):
        r = InvokeConnectionResponse(data={"key": "val"}, metadata={"m": 1}, errors=None)
        self.assertIn("ConnectionResponse", repr(r))

    def test_str(self):
        r = InvokeConnectionResponse(data={"key": "val"})
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = InvokeConnectionResponse()
        self.assertIsNone(r.data)
        self.assertEqual(r.metadata, {})
        self.assertIsNone(r.errors)

    def test_metadata_defaults_to_empty_dict_when_falsy(self):
        r = InvokeConnectionResponse(metadata=None)
        self.assertEqual(r.metadata, {})


if __name__ == "__main__":
    unittest.main()
