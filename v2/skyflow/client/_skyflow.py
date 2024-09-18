from typing import List, Optional
from v2.skyflow.management.config import ManagementConfig
from v2.skyflow.utils import LogLevel
from v2.skyflow.vault.config import VaultConfig, CredentialsConfig, ConnectionConfig


class Skyflow:
    def __init__(self,
                 vault_config: List[VaultConfig],
                 skyflow_credentials: Optional[CredentialsConfig],
                 connection_config: Optional[List[ConnectionConfig]] = None,
                 log_level: Optional[LogLevel] = None):
        self.vault_config = vault_config
        self.skyflow_credentials = skyflow_credentials
        self.connection_config = connection_config
        self.log_level = log_level

    @classmethod
    def builder(cls):
        return cls._Builder()

    class _Builder:
        def __init__(self):
            self._vault_config = []
            self._connection_config = []
            self._skyflow_credentials = None
            self._log_level = None

        def add_vault_config(self, vault_config: VaultConfig):
            pass

        def remove_vault_config(self, vault_id: str):
            pass

        def update_vault_config(self, vault_config: VaultConfig):
            pass

        def add_connection_config(self, connection_config: ConnectionConfig):
            pass

        def remove_connection_config(self, connection_id: str):
            pass

        def update_connection_config(self, connection_config: ConnectionConfig):
            pass

        def update_log_level(self, log_level: LogLevel):
            pass

        def log_level(self, log_level: str):
            pass

        def build(self):
            pass

        def vault(self, vault_id: str):
            pass

        def connection(self, connection_id: str):
            pass