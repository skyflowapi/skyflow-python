from enum import Enum


class Configuration:
    def __init__(self, vaultID: str, vaultURL: str, tokenProvider):
        self.vaultID = vaultID
        self.vaultURL = vaultURL
        self.tokenProvider = tokenProvider

class InsertOptions:
    def __init__(self, tokens: bool=True):
        self.tokens = tokens

class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'

class GatewayConfig:
    def __init__(self, gatewayURL: str, methodName: RequestMethod, 
    pathParams: dict={}, queryParams: dict={}, requestHeader: dict={}, requestBody: dict={}):
        self.gatewayURL = gatewayURL.rstrip("/")
        self.methodName = methodName
        self.pathParams = pathParams
        self.queryParams = queryParams
        self.requestHeader = requestHeader
        self.requestBody = requestBody

class RedactionType(Enum):
    PLAIN_TEXT = "PLAIN_TEXT"
    MASKED = "MASKED"
    REDACTED = "REDACTED"
    DEFAULT = "DEFAULT"
