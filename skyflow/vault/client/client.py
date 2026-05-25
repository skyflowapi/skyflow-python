from skyflow.error import SkyflowError
from skyflow.generated.rest.client import Skyflow
from skyflow.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired
from skyflow.utils import get_vault_url, get_credentials, SkyflowMessages
from skyflow.utils.logger import log_info
from skyflow.utils.constants import OptionField, CredentialField, ConfigField


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
        self.__credentials = None
        self.__vault_url = None
        self.__is_static_token = None

    def set_common_skyflow_credentials(self, credentials):
        self.__common_skyflow_credentials = credentials

    def set_logger(self, log_level, logger):
        self.__log_level = log_level
        self.__logger = logger

    def initialize_client_configuration(self):
        if self.__api_client is not None and not self.__is_config_updated:
            if self.__is_static_token:
                return
            if self.__bearer_token is not None and not is_expired(self.__bearer_token):
                return

        needs_reinit = self.__api_client is None or self.__is_config_updated
        if needs_reinit:
            self.__credentials = get_credentials(self.__config.get(ConfigField.CREDENTIALS), self.__common_skyflow_credentials, logger=self.__logger)
            self.__vault_url = get_vault_url(self.__config.get(ConfigField.CLUSTER_ID),
                                             self.__config.get(ConfigField.ENV),
                                             self.__config.get(ConfigField.VAULT_ID),
                                             logger=self.__logger)
            self.__is_static_token = CredentialField.TOKEN in self.__credentials or CredentialField.API_KEY in self.__credentials
        bearer_token = self.get_bearer_token(self.__credentials)
        if needs_reinit:
            self.initialize_api_client(self.__vault_url, bearer_token)

    def initialize_api_client(self, vault_url, bearer_token):
        token_provider = lambda: self.__bearer_token if self.__bearer_token is not None else bearer_token  # noqa: E731
        self.__api_client = Skyflow(base_url=vault_url, token=token_provider)

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
        return self.__config.get(ConfigField.VAULT_ID)

    def get_bearer_token(self, credentials):
        if CredentialField.API_KEY in credentials:
            return credentials.get(CredentialField.API_KEY)
        elif CredentialField.TOKEN in credentials:
            return credentials.get(CredentialField.TOKEN)

        options = {
            OptionField.ROLE_IDS: self.__config.get(OptionField.ROLES),
            OptionField.CTX: self.__config.get(OptionField.CTX)
        }
        if CredentialField.TOKEN_URI_OPTION in credentials and credentials.get(CredentialField.TOKEN_URI_OPTION):
            options[CredentialField.TOKEN_URI_OPTION] = credentials.get(CredentialField.TOKEN_URI_OPTION)

        if self.__bearer_token is None or self.__is_config_updated or is_expired(self.__bearer_token):
            if CredentialField.PATH in credentials:
                self.__bearer_token, _ = generate_bearer_token(
                    credentials.get(CredentialField.PATH),
                    options,
                    self.__logger
                )
            else:
                credentials_string = credentials.get(CredentialField.CREDENTIALS_STRING)
                log_info(SkyflowMessages.Info.GENERATE_BEARER_TOKEN_FROM_CREDENTIALS_STRING_TRIGGERED.value, self.__logger)
                self.__bearer_token, _ = generate_bearer_token_from_creds(
                    credentials_string,
                    options,
                    self.__logger
                )
            self.__is_config_updated = False
        else:
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