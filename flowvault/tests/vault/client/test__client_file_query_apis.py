import unittest
from unittest.mock import MagicMock

from skyflow.vault.client.client import VaultClient


class TestVaultClientFileAndQueryApis(unittest.TestCase):
    def setUp(self):
        self.vault_client = VaultClient({"vault_id": "test_vault"})

    def test_get_query_api_returns_query(self):
        self.vault_client._api_client = MagicMock()
        self.assertEqual(self.vault_client.get_query_api(), self.vault_client._api_client.query)

    def test_get_files_api_returns_files(self):
        self.vault_client._api_client = MagicMock()
        self.assertEqual(self.vault_client.get_files_api(), self.vault_client._api_client.files)

    def test_put_signed_url_sends_content_and_content_type(self):
        http_client = MagicMock()
        http_client.put.return_value = "put-result"
        self.vault_client._sync_httpx_client = http_client

        result = self.vault_client.put_signed_url("https://signed/url", b"bytes", "application/pdf")

        self.assertEqual(result, "put-result")
        _, kwargs = http_client.put.call_args
        args, _ = http_client.put.call_args
        self.assertEqual(args[0], "https://signed/url")
        self.assertEqual(kwargs["content"], b"bytes")
        self.assertEqual(kwargs["headers"], {"content-type": "application/pdf"})

    def test_put_signed_url_without_content_type_sends_empty_headers(self):
        http_client = MagicMock()
        self.vault_client._sync_httpx_client = http_client

        self.vault_client.put_signed_url("https://signed/url", b"bytes")

        _, kwargs = http_client.put.call_args
        self.assertEqual(kwargs["headers"], {})


if __name__ == "__main__":
    unittest.main()
