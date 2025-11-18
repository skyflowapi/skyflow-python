from skyflow.generated.rest.client import Skyflow
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
        credentials = get_credentials(self.__config.get("credentials"), self.__common_skyflow_credentials, logger = self.__logger)
        token = self.get_bearer_token(credentials)
        vault_url = get_vault_url(self.__config.get("cluster_id"),
                                  self.__config.get("env"),
                                  self.__config.get("vault_id"),
                                  logger = self.__logger)
        self.initialize_api_client(vault_url, token)

    def initialize_api_client(self, vault_url, token):
        self.__api_client =  Skyflow(base_url=vault_url, token=token)

    def get_records_api(self):
        return self.__api_client.records

    def get_tokens_api(self):
        return self.__api_client.tokens

    def get_query_api(self):
        return self.__api_client.query
    
    def get_detect_text_api(self):
        return self.__api_client.strings
    
    def get_detect_file_api(self):
        return self.__api_client.files

    def get_vault_id(self):
        return self.__config.get("vault_id")

    def get_bearer_token(self, credentials):
        if 'api_key' in credentials:
            return credentials.get('api_key')
        elif 'token' in credentials:
            return credentials.get("token")

        options = {
            "role_ids": self.__config.get("roles"),
            "ctx": self.__config.get("ctx")
        }

        if self.__bearer_token is None or self.__is_config_updated:
            if 'path' in credentials:
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
        else:
            log_info(SkyflowMessages.Info.REUSE_BEARER_TOKEN.value, self.__logger)

        if is_expired(self.__bearer_token):
            self.__is_config_updated = True
            raise SyntaxError(SkyflowMessages.Error.EXPIRED_TOKEN.value, SkyflowMessages.ErrorCodes.INVALID_INPUT.value)

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