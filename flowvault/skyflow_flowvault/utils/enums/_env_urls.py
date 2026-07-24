from enum import Enum


class EnvUrls(Enum):
    """v3 vault hosts -- a different subdomain than v2 (skyvault vs. vault). All four confirmed."""
    DEV = "skyvault.skyflowapis.dev"
    PROD = "skyvault.skyflowapis.com"
    SANDBOX = "skyvault.skyflowapis-preview.com"
    STAGE = "skyvault.skyflowapis.tech"
