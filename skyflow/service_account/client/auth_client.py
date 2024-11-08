from skyflow.generated.rest import Configuration, ApiClient
from skyflow.generated.rest.api import AuthenticationApi


class AuthClient:
    def __init__(self, url):
        self.__url = url
        self.__client_configuration = self.initialize_client_configuration()
        self.__api_client = self.initialize_api_client()

    def initialize_client_configuration(self):
        return  Configuration(host=self.__url)

    def initialize_api_client(self):
        return ApiClient(self.__client_configuration)

    def get_auth_api(self):
        return AuthenticationApi(self.__api_client)