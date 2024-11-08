# coding: utf-8

"""
    Skyflow Data API

    # Data API  This API inserts, retrieves, and otherwise manages data in a vault.  The Data API is available from two base URIs. *identifier* is the identifier in your vault's URL.<ul><li><b>Sandbox:</b> https://*identifier*.vault.skyflowapis-preview.com</li><li><b>Production:</b> https://*identifier*.vault.skyflowapis.com</li></ul>  When you make an API call, you need to add a header: <table><tr><th>Header</th><th>Value</th><th>Example</th></tr><tr><td>Authorization</td><td>A Bearer Token. See <a href='/api-authentication/'>API Authentication</a>.</td><td><code>Authorization: Bearer eyJhbGciOiJSUzI...1NiIsJdfPA</code></td></tr><table/>

    The version of the OpenAPI document: v1
    Contact: support@skyflow.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import json
from enum import Enum
from typing_extensions import Self


class AuditEventAuditResourceType(str, Enum):
    """
    Type of the resource.
    """

    """
    allowed enum values
    """
    NONE_API = 'NONE_API'
    ACCOUNT = 'ACCOUNT'
    AUDIT = 'AUDIT'
    BASE_DATA_TYPE = 'BASE_DATA_TYPE'
    FIELD_TEMPLATE = 'FIELD_TEMPLATE'
    FILE = 'FILE'
    KEY = 'KEY'
    POLICY = 'POLICY'
    PROTO_PARSE = 'PROTO_PARSE'
    RECORD = 'RECORD'
    ROLE = 'ROLE'
    RULE = 'RULE'
    SECRET = 'SECRET'
    SERVICE_ACCOUNT = 'SERVICE_ACCOUNT'
    TOKEN = 'TOKEN'
    USER = 'USER'
    VAULT = 'VAULT'
    VAULT_TEMPLATE = 'VAULT_TEMPLATE'
    WORKSPACE = 'WORKSPACE'
    TABLE = 'TABLE'
    POLICY_TEMPLATE = 'POLICY_TEMPLATE'
    MEMBER = 'MEMBER'
    TAG = 'TAG'
    CONNECTION = 'CONNECTION'
    MIGRATION = 'MIGRATION'
    SCHEDULED_JOB = 'SCHEDULED_JOB'
    JOB = 'JOB'
    COLUMN_NAME = 'COLUMN_NAME'
    NETWORK_TOKEN = 'NETWORK_TOKEN'
    SUBSCRIPTION = 'SUBSCRIPTION'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of AuditEventAuditResourceType from a JSON string"""
        return cls(json.loads(json_str))

