from v2.skyflow.utils import LogLevel

class Skyflow:
    def __init__(self,
                 vault_config,
                 skyflow_credentials = [],
                 connection_config = [],
                 log_level = LogLevel.ERROR):
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

        def add_vault_config(self, vault_config):
            self._vault_config.append(vault_config)
            return self

        def remove_vault_config(self, vault_id):
            pass

        def update_vault_config(self, vault_config):
            pass

        def add_connection_config(self, connection_config):
            pass

        def remove_connection_config(self, connection_id):
            pass

        def update_connection_config(self, connection_config):
            pass

        def update_log_level(self, log_level):
            pass

        def set_log_level(self, log_level):
            pass

        def build(self):
            pass

        def vault(self, vault_id):
            pass

        def connection(self, connection_id):
            pass