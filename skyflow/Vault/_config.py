from enum import Enum
from types import FunctionType
from warnings import warn


class Configuration:
    def __init__(self, vaultID: str, vaultURL: str, tokenProvider: FunctionType):
        warn('This constructor has been deprecated, please use Configuration(tokenProvider, vaultID="", vaultURL="")', DeprecationWarning)
        self.vaultID = vaultID
        self.vaultURL = vaultURL
        self.tokenProvider = tokenProvider
        
    def __init__(self, tokenProvider: FunctionType, vaultID: str="", vaultURL: str=""):
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

class ConnectionConfig:
    def __init__(self, connectionURL: str, methodName: RequestMethod, 
    pathParams: dict={}, queryParams: dict={}, requestHeader: dict={}, requestBody: dict={}):
        self.connectionURL = connectionURL.rstrip("/")
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
