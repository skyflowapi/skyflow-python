from abc import ABC, abstractmethod

from common.service_account import generate_bearer_token, generate_bearer_token_from_creds, is_expired
from common.utils import get_credentials, SkyflowMessages
from common.utils.logger import log_info
from common.utils.constants import OptionField, CredentialField, ConfigField


class IVaultClient(ABC):
    @abstractmethod
    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        raise NotImplementedError

    @abstractmethod
    def initialize_api_client(self, vault_url, bearer_token):
        raise NotImplementedError


class BaseVaultClient(IVaultClient):
    def __init__(self, config):
        self._config = config
        self._common_skyflow_credentials = None
        self._log_level = None
        self._api_client = None
        self._logger = None
        self._is_config_updated = False
        self._bearer_token = None
        self._credentials = None
        self._vault_url = None
        self._is_static_token = None

    def set_common_skyflow_credentials(self, credentials):
        self._common_skyflow_credentials = credentials

    def set_logger(self, log_level, logger):
        self._log_level = log_level
        self._logger = logger

    def initialize_client_configuration(self):
        if self._api_client is not None and not self._is_config_updated:
            if self._is_static_token:
                return
            if self._bearer_token is not None and not is_expired(self._bearer_token):
                return

        needs_reinit = self._api_client is None or self._is_config_updated
        if needs_reinit:
            self._credentials = get_credentials(self._config.get(ConfigField.CREDENTIALS), self._common_skyflow_credentials, logger=self._logger)
            self._vault_url = self.resolve_vault_url(self._config.get(ConfigField.CLUSTER_ID),
                                                       self._config.get(ConfigField.ENV),
                                                       self._config.get(ConfigField.VAULT_ID),
                                                       logger=self._logger)
            self._is_static_token = CredentialField.TOKEN in self._credentials or CredentialField.API_KEY in self._credentials
        bearer_token = self.get_bearer_token(self._credentials)
        self._bearer_token = bearer_token
        if needs_reinit:
            self.initialize_api_client(self._vault_url, bearer_token)

    def get_current_bearer_token(self):
        return self._bearer_token

    def get_current_vault_url(self):
        return self._vault_url

    def get_vault_id(self):
        return self._config.get(ConfigField.VAULT_ID)

    def get_bearer_token(self, credentials):
        if CredentialField.API_KEY in credentials:
            return credentials.get(CredentialField.API_KEY)
        elif CredentialField.TOKEN in credentials:
            return credentials.get(CredentialField.TOKEN)

        options = {
            OptionField.ROLE_IDS: self._config.get(OptionField.ROLES),
            OptionField.CTX: self._config.get(OptionField.CTX)
        }
        if CredentialField.TOKEN_URI_OPTION in credentials and credentials.get(CredentialField.TOKEN_URI_OPTION):
            options[CredentialField.TOKEN_URI_OPTION] = credentials.get(CredentialField.TOKEN_URI_OPTION)

        if self._bearer_token is None or self._is_config_updated or is_expired(self._bearer_token):
            if CredentialField.PATH in credentials:
                self._bearer_token, _ = generate_bearer_token(
                    credentials.get(CredentialField.PATH),
                    options,
                    self._logger
                )
            else:
                credentials_string = credentials.get(CredentialField.CREDENTIALS_STRING)
                log_info(SkyflowMessages.Info.GENERATE_BEARER_TOKEN_FROM_CREDENTIALS_STRING_TRIGGERED.value, self._logger)
                self._bearer_token, _ = generate_bearer_token_from_creds(
                    credentials_string,
                    options,
                    self._logger
                )
            self._is_config_updated = False
        else:
            log_info(SkyflowMessages.Info.REUSE_BEARER_TOKEN.value, self._logger)

        return self._bearer_token

    def update_config(self, config):
        self._config.update(config)
        self._is_config_updated = True

    def get_config(self):
        return self._config

    def get_common_skyflow_credentials(self):
        return self._common_skyflow_credentials

    def get_log_level(self):
        return self._log_level

    def get_logger(self):
        return self._logger
