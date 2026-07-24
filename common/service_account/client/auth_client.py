from common.generated.rest.client import SkyflowAuth
from common.utils.constants import OPTIONAL_TOKEN

class AuthClient:
    def __init__(self, url):
        self.__url = url
        self.__api_client = self.initialize_api_client()

    def initialize_api_client(self):
        return SkyflowAuth(base_url=self.__url, token=OPTIONAL_TOKEN)

    def get_auth_api(self):
        return self.__api_client.authentication
