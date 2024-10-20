from skyflow.generated.rest import Configuration, RecordsApi, ApiClient, TokensApi, QueryApi
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds
from skyflow.utils import get_vault_url, get_credentials, SkyflowMessages, log_info


class VaultClient:
    def __init__(self, config):
        self.__config = config
        self.__common_skyflow_credentials = None
        self.__log_level = None
        self.__client_configuration = None
        self.__api_client = None
        self.__logger = None

    def set_common_skyflow_credentials(self, credentials):
        self.__common_skyflow_credentials = credentials

    def set_logger(self, log_level, logger):
        self.__log_level = log_level
        self.__logger = logger

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
        interface = SkyflowMessages.InterfaceName.GENERATE_BEARER_TOKEN.value
        if 'api_key' in credentials:
            return credentials.get('api_key')
        elif 'token' in credentials:
            return credentials.get("token")
        elif 'path' in credentials:
            credentials = self.__config.get("credentials")
            options = {
                "role_ids": self.__config.get("roles"),
                "ctx": self.__config.get("ctx")
            }
            log_info(self.__logger, SkyflowMessages.Info.GENERATE_BEARER_TOKEN_TRIGGERED, interface)
            token, _ = generate_bearer_token(credentials.get("path"), options, self.__logger)
            log_info(self.__logger, SkyflowMessages.Info.GENERATE_BEARER_TOKEN_SUCCESS, interface)
            return token
        else:
            credentials = self.__config.get("credentials")
            options = {
                "role_ids": self.__config.get("roles"),
                "ctx": self.__config.get("ctx")
            }
            log_info(self.__logger, SkyflowMessages.Info.GENERATE_BEARER_TOKEN_TRIGGERED, interface)
            token, _ = generate_bearer_token_from_creds(credentials.get("credentials_string"), options, self.__logger)
            log_info(self.__logger, SkyflowMessages.Info.GENERATE_BEARER_TOKEN_SUCCESS, interface)
            return token

    def update_config(self, config):
        self.__config.update(config)

    def get_config(self):
        return self.__config

    def get_common_skyflow_credentials(self):
        return self.__common_skyflow_credentials

    def get_log_level(self):
        return self.__log_level

    def get_logger(self):
        return self.__logger