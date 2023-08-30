'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from enum import Enum
from types import FunctionType
from typing import List


class Configuration:
    '''
        Configuration for interacting with Skyflow.

        :param vaultID: ID of the vault to connect to.
        :param vaultURL: URL of the vault to connect to.
        :param tokenProvider: Token provider for authentication.
    '''
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

class UpsertOption:
    '''
        Configuration for upsert.

        :param table: Table that the data belongs to.
        :param column: Name of the unique column.
    '''
    def __init__(self,table: str,column: str):
        self.table = table
        self.column = column

class InsertOptions:
    '''
        Configuration for an insert operation.

        :param tokens: If `true`, returns tokens for the collected data. Defaults to `false`.
        :param upsert: If specified, upserts data. If not specified, inserts data.
    '''
    def __init__(self, tokens: bool=True,upsert :List[UpsertOption]=None):
        self.tokens = tokens
        self.upsert = upsert

class UpdateOptions:
    '''
        Updates the configuration of elements in the vault.

        :param tokens: If `true`, returns tokens for the collected data. Defaults to `false`.
    '''
    def __init__(self, tokens: bool=True):
        self.tokens = tokens

class RequestMethod(Enum):
    '''
        Supported request methods.
    '''
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'

class ConnectionConfig:
    '''
        Configuration for making a connection to an external service.

        :param connectionURL: URL for the connection.
        :param methodName: HTTP request method to use.
        :param pathParams: Parameters to include in the URL path. Defaults to an empty dictionary.
        :param queryParams: Parameters to include in the URL query. Defaults to an empty dictionary.
        :param requestHeader: Headers for the request. Defaults to an empty dictionary.
        :param requestBody: The body of the request. Defaults to an empty dictionary.
    '''
    def __init__(self, connectionURL: str, methodName: RequestMethod, 
    pathParams: dict={}, queryParams: dict={}, requestHeader: dict={}, requestBody: dict={}):
        self.connectionURL = connectionURL.rstrip("/")
        self.methodName = methodName
        self.pathParams = pathParams
        self.queryParams = queryParams
        self.requestHeader = requestHeader
        self.requestBody = requestBody

class RedactionType(Enum):
    '''
        Supported redaction types.
    '''
    PLAIN_TEXT = "PLAIN_TEXT"
    MASKED = "MASKED"
    REDACTED = "REDACTED"
    DEFAULT = "DEFAULT"
