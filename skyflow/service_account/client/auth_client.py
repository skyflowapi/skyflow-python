from skyflow.generated.rest.client import Skyflow

class AuthClient:
    def __init__(self, url):
        self.__url = url
        self.__api_client = self.initialize_api_client()

    def initialize_api_client(self):
        return Skyflow(base_url=self.__url, token='')

    def get_auth_api(self):
        return self.__api_client.authentication