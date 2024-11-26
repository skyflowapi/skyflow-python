from enum import Enum

class Env(Enum):
    DEV = 'DEV',
    SANDBOX = 'SANDBOX',
    PROD = 'PROD'

class EnvUrls(Enum):
    PROD = "vault.skyflowapis.com",
    SANDBOX = "vault.skyflowapis-preview.com",
    DEV = "vault.skyflowapis.dev"