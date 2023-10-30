'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from enum import Enum
from types import FunctionType
from typing import List


class Configuration:

    def __init__(self, vaultID: str = None, vaultURL: str = None, tokenProvider: FunctionType = None):

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

class BYOT(Enum):
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    ENABLE_STRICT = "ENABLE_STRICT"
    
class UpsertOption:
    def __init__(self, table: str, column: str):
        self.table = table
        self.column = column


class InsertOptions:
    def __init__(self, tokens: bool=True, upsert :List[UpsertOption]=None, continueOnError:bool=None, byot:BYOT=BYOT.DISABLE):
        self.tokens = tokens
        self.upsert = upsert
        self.continueOnError = continueOnError
        self.byot = byot


class UpdateOptions:
    def __init__(self, tokens: bool = True):
        self.tokens = tokens

class GetOptions:
    def __init__(self, tokens: bool = False):
        self.tokens = tokens

class DeleteOptions:
    def __init__(self, tokens: bool=False):
        self.tokens = tokens
        
class QueryOptions:
    def __init__(self):
        pass

class DetokenizeOptions:
    def __init__(self, continueOnError: bool=True):
        self.continueOnError = continueOnError

class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class ConnectionConfig:
    def __init__(self, connectionURL: str, methodName: RequestMethod,
                 pathParams: dict = {}, queryParams: dict = {}, requestHeader: dict = {}, requestBody: dict = {}):
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
