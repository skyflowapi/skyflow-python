'''
	Copyright (c) 2022 Skyflow, Inc.
'''
from enum import Enum
from types import FunctionType
from typing import List


class Configuration:
    '''
        This is the documentation for Configuration class

        :param vaultID: This is the description for vaultID parameter
        :param vaultURL: This is the description for vaultURL parameter
        :param tokenProvider: This is the description for tokenProvider parameter
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
        This is the documentation for UpsertOption class

        :param table: This is the description for table parameter
        :param column: This is the description for column parameter
    '''
    def __init__(self,table: str,column: str):
        self.table = table
        self.column = column

class InsertOptions:
    '''
        This is the documentation for InsertOptions class

        :param tokens: This is the description for tokens parameter
        :param upsert: This is the description for upsert parameter
    '''
    def __init__(self, tokens: bool=True,upsert :List[UpsertOption]=None):
        self.tokens = tokens
        self.upsert = upsert

class UpdateOptions:
    '''
        This is the documentation for UpdateOptions class

        :param tokens: This is the description for tokens parameter
    '''
    def __init__(self, tokens: bool=True):
        self.tokens = tokens

class RequestMethod(Enum):
    '''
        This is the documentation for RequestMethod enum class
    '''
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'

class ConnectionConfig:
    '''
        This is the documentation for ConnectionConfig class

        :param connectionURL: This is the description for connectionURL parameter
        :param methodName: This is the description for methodName parameter
        :param pathParams: This is the description for pathParams parameter
        :param queryParams: This is the description for queryParams parameter
        :param requestHeader: This is the description for requestHeader parameter
        :param requestBody: This is the description for requestBody parameter
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
        This is the documentation for RedactionType enum class
    '''
    PLAIN_TEXT = "PLAIN_TEXT"
    MASKED = "MASKED"
    REDACTED = "REDACTED"
    DEFAULT = "DEFAULT"
