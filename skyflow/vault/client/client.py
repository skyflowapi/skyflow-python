import json
from skyflow.generated.rest import Configuration, RecordsApi, ApiClient, TokensApi, QueryApi
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired
from skyflow.utils import get_vault_url, get_credentials, SkyflowMessages
from skyflow.utils.logger import log_info


class VaultClient:
    def __init__(self, config):
        self.__config = config
        self.__common_skyflow_credentials = None
        self.__log_level = None
        self.__client_configuration = None
        self.__api_client = None
        self.__logger = None
        self.__is_config_updated = False
        self.__bearer_token = None

    def set_common_skyflow_credentials(self, credentials):
        self.__common_skyflow_credentials = credentials

    def set_logger(self, log_level, logger):
        self.__log_level = log_level
        self.__logger = logger

    def initialize_client_configuration(self):
        credentials, env_creds  = get_credentials(self.__config.get("credentials"), self.__common_skyflow_credentials, logger = self.__logger)
        token = self.get_bearer_token(credentials, env_creds)
        vault_url = get_vault_url(self.__config.get("cluster_id"),
                                  self.__config.get("env"),
                                  self.__config.get("vault_id"),
                                  logger = self.__logger)
        self.__client_configuration = Configuration(host=vault_url, access_token=token)
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

    def get_bearer_token(self, credentials, env_creds):
        if 'api_key' in credentials:
            return credentials.get('api_key')
        elif 'token' in credentials:
            return credentials.get("token")

        options = {
            "role_ids": self.__config.get("roles"),
            "ctx": self.__config.get("ctx")
        }

        if self.__bearer_token is None or self.__is_config_updated:
            if env_creds:
                log_info(SkyflowMessages.Info.GENERATE_BEARER_TOKEN_FROM_CREDENTIALS_STRING_TRIGGERED.value,
                         self.__logger)
                self.__bearer_token, _ = generate_bearer_token_from_creds(
                    json.dumps(credentials),
                    options,
                    self.__logger
                )
            elif 'path' in credentials:
                path = credentials.get("path")
                self.__bearer_token, _ = generate_bearer_token(
                    path,
                    options,
                    self.__logger
                )
            else:
                credentials_string = credentials.get('credentials_string')
                log_info(SkyflowMessages.Info.GENERATE_BEARER_TOKEN_FROM_CREDENTIALS_STRING_TRIGGERED.value, self.__logger)
                self.__bearer_token, _ = generate_bearer_token_from_creds(
                    credentials_string,
                    options,
                    self.__logger
                )
            self.__is_config_updated = False

        if is_expired(self.__bearer_token):
            self.__is_config_updated = True
            raise SyntaxError(SkyflowMessages.Error.EXPIRED_TOKEN.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

        log_info(SkyflowMessages.Info.REUSE_BEARER_TOKEN.value, self.__logger)
        return self.__bearer_token

    def update_config(self, config):
        self.__config.update(config)
        self.__is_config_updated = True

    def get_config(self):
        return self.__config

    def get_common_skyflow_credentials(self):
        return self.__common_skyflow_credentials

    def get_log_level(self):
        return self.__log_level

    def get_logger(self):
        return self.__logger