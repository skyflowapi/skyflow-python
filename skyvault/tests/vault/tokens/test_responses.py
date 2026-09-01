import unittest
from skyflow.vault.tokens._detokenize_response import DetokenizeResponse
from skyflow.vault.tokens._tokenize_response import TokenizeResponse


class TestDetokenizeResponse(unittest.TestCase):
    def test_repr(self):
        r = DetokenizeResponse(detokenized_fields=[{"token": "t1", "value": "v1"}], errors=None)
        self.assertIn("DetokenizeResponse", repr(r))
        self.assertIn("t1", repr(r))

    def test_str(self):
        r = DetokenizeResponse(detokenized_fields=[{"token": "t1"}])
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = DetokenizeResponse()
        self.assertIsNone(r.detokenized_fields)
        self.assertIsNone(r.errors)


class TestTokenizeResponse(unittest.TestCase):
    def test_repr(self):
        r = TokenizeResponse(tokenized_fields=[{"value": "val", "token": "tok"}], errors=None)
        self.assertIn("TokenizeResponse", repr(r))

    def test_str(self):
        r = TokenizeResponse(tokenized_fields=[{"token": "tok"}])
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = TokenizeResponse()
        self.assertIsNone(r.tokenized_fields)
        self.assertIsNone(r.errors)


if __name__ == "__main__":
    unittest.main()
