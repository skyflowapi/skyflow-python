import unittest
from skyflow.utils import get_base_url, format_scope, is_valid_url

VALID_URL = "https://example.com/path?query=1"
BASE_URL = "https://example.com"
EMPTY_URL = ""
INVALID_URL = "invalid-url"
SCOPES_LIST = ["admin", "user", "viewer"]
FORMATTED_SCOPES = "role:admin role:user role:viewer"

class TestHelperFunctions(unittest.TestCase):
    def test_get_base_url_valid_url(self):
        self.assertEqual(get_base_url(VALID_URL), BASE_URL)

    def test_get_base_url_empty_url(self):
        self.assertEqual(get_base_url(EMPTY_URL), "://")

    def test_get_base_url_invalid_url(self):
        self.assertEqual(get_base_url(INVALID_URL), "://")

    def test_format_scope_valid_scopes(self):
        self.assertEqual(format_scope(SCOPES_LIST), FORMATTED_SCOPES)

    def test_format_scope_empty_list(self):
        self.assertIsNone(format_scope([]))

    def test_format_scope_none(self):
        self.assertIsNone(format_scope(None))

    def test_format_scope_single_scope(self):
        single_scope = ["admin"]
        expected_result = "role:admin"
        self.assertEqual(format_scope(single_scope), expected_result)

    def test_format_scope_special_characters(self):
        scopes_with_special_chars = ["admin", "user:write", "read-only"]
        expected_result = "role:admin role:user:write role:read-only"
        self.assertEqual(format_scope(scopes_with_special_chars), expected_result)

    def test_is_valid_url_valid(self):
        self.assertTrue(is_valid_url("https://example.com"))
        self.assertTrue(is_valid_url("http://example.com/path"))

    def test_is_valid_url_invalid(self):
        self.assertFalse(is_valid_url("ftp://example.com"))
        self.assertFalse(is_valid_url("example.com"))
        self.assertFalse(is_valid_url("invalid-url"))
        self.assertFalse(is_valid_url(""))

    def test_is_valid_url_none(self):
        self.assertFalse(is_valid_url(None))

    def test_is_valid_url_no_scheme(self):
        self.assertFalse(is_valid_url("www.example.com"))