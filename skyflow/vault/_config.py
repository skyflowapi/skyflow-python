from enum import Enum
from types import FunctionType
from typing import OrderedDict


class Configuration:

    def __init__(self, vaultID: str=None, vaultURL: str=None, tokenProvider: FunctionType=None):
        
        self.vaultID = ''
        self.vaultURL = ''
          
        if tokenProvider == None and vaultURL == None and isinstance(vaultID, FunctionType):
            self.tokenProvider = vaultID
        elif tokenProvider == None and vaultID == None and isinstance(vaultURL, FunctionType):
            self.tokenProvider = vaultURL
        else:
            if tokenProvider is None:
                raise TypeError('tokenProvider must be given')
            self.vaultID = vaultID or ""
            self.vaultURL = vaultURL or ""
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
