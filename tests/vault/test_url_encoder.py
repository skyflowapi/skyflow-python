'''
	Copyright (c) 2022 Skyflow, Inc.
'''
import platform
import sys
import unittest
from skyflow._utils import http_build_query, getMetrics
from version import SDK_VERSION

class TestUrlEncoder(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_encoder_simple(self):
        data = {
            "key": "value"
        }

        http_data = http_build_query(data)
        self.assertEqual(http_data, "key=value")

    def test_encoder_multiplekeys(self):
        data = {
            "key": "value",
            "key2": "value2"
        }

        http_data = http_build_query(data)
        self.assertEqual(http_data, "key=value&key2=value2")

    def test_encoder_nested(self):
        data = {
            "key": "value",
            "nested": {
                "key": "value"
            }
        }

        http_data = http_build_query(data)

        self.assertEqual(http_data, "key=value&nested%5Bkey%5D=value")

    def test_encoder_array(self):
        data = {
            "key": "value",
            "nested": {
                "array": ["one", "two"],
                "key": "value"
            }
        }
        http_data = http_build_query(data)

        self.assertEqual(
            http_data, "key=value&nested%5Barray%5D%5B0%5D=one&nested%5Barray%5D%5B1%5D=two&nested%5Bkey%5D=value")

    def test_get_metrics(self):
        expected = {
            'sdk_name_version': "skyflow-python@" + SDK_VERSION, 
            'sdk_client_device_model': platform.node(),
            'sdk_client_os_details': sys.platform,
            'sdk_runtime_details': sys.version,
        }
        actual = getMetrics()
        self.assertEqual(actual, expected)