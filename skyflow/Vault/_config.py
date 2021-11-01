from enum import Enum


class SkyflowConfiguration:
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
    pathParams: dict={}, queryParams: dict={}, requestHeader: dict={}, requestBody: dict={}, responseBody: dict={}):
        self.gatewayURL = gatewayURL
        self.methodName = methodName
        self.pathParams = pathParams
        self.queryParams = queryParams
        self.requestHeader = requestHeader
        self.requestBody = requestBody
        self.responseBody = responseBody
