from skyflow.generated.rest import Configuration, RecordsApi, ApiClient, TokensApi, QueryApi
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds
from skyflow.utils import get_vault_url, get_credentials


class VaultClient:
    __common_skyflow_credentials = None
    __log_level = None
    def __init__(self, config):
        self.__config = config
        self.__client_configuration = None
        self.__api_client = None

    @staticmethod
    def set_common_skyflow_credentials(credentials):
        VaultClient.__common_skyflow_credentials = credentials

    @staticmethod
    def set_log_level(log_level):
        VaultClient.__log_level = log_level

    def initialize_client_configuration(self):
        credentials  = get_credentials(self.__config.get("credentials"), self.__common_skyflow_credentials)
        bearer_token = self.get_bearer_token(credentials)
        vault_url = get_vault_url(self.__config.get("cluster_id"),
                                  self.__config.get("env"))
        self.__client_configuration = Configuration(host=vault_url, access_token=bearer_token)
        self.initialize_api_client(self.__client_configuration)

    def initialize_api_client(self, config):
        self.__api_client =  ApiClient(config)

    def get_records_api(self):
        return RecordsApi(self.__api_client)

    def get_tokens_api(self):
        return TokensApi(self.__api_client)

    def get_query_api(self):
        return QueryApi(self.__api_client)

    def get_vault_id(self):
        return self.__config.get("vault_id")

    def get_bearer_token(self, credentials):
        if 'token' in credentials:
            return credentials.get("token")
        elif 'path' in credentials:
            credentials = self.__config.get("credentials")
            roles = self.__config.get("roles") if "roles" in self.__config else None
            return generate_bearer_token(credentials.get("path"), roles)
        else:
            credentials = self.__config.get("credentials")
            roles = self.__config.get("roles") if "roles" in self.__config else None
            return generate_bearer_token_from_creds(credentials.get("credentials_string"), roles)

    def update_config(self, config):
        self.__config.update(config)

    def get_config(self):
        return self.__config

    @staticmethod
    def get_common_skyflow_credentials():
        return VaultClient.__common_skyflow_credentials

    @staticmethod
    def get_log_level():
        return VaultClient.__log_level