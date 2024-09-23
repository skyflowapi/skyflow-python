from v2.skyflow.client._skyflow_builder import Builder

class Skyflow:
    def __init__(self, builder):
        self.builder = builder

    @staticmethod
    def builder():
        return Builder()

    def add_vault_config(self, config):
        self.builder.add_vault_config(config)
        return self

    def remove_vault_config(self, vault_id):
        self.builder.remove_vault_config(vault_id)
        return self

    def update_vault_config(self,config):
        self.builder.update_vault_config(config)
        return self

    def get_vault_config(self, vault_id):
        self.builder.get_vault_config(vault_id)
        return self

    def add_connection_config(self, config):
        self.builder.add_connection_config(config)
        return self

    def remove_connection_config(self, connection_id):
        self.builder.remove_connection_config(connection_id)
        return self

    def update_connection_config(self, config):
        self.builder.update_connection_config(config)
        return self

    def get_connection_config(self, connection_id):
        self.builder.get_connection_config(connection_id)
        return self

    def add_skyflow_credentials(self, credentials):
        self.builder.add_skyflow_credentials(credentials)
        return self

    def update_skyflow_credentials(self, credentials):
        self.builder.add_skyflow_credentials(credentials)
        return self

    def get_skyflow_credentials(self):
        return self.builder.get_skyflow_credentials()

    def set_log_level(self, log_level):
        self.builder.set_log_level(log_level)
        return self

    def update_log_level(self, log_level):
        self.builder.set_log_level(log_level)
        return self

    def get_log_level(self):
        return self.builder.log_level

    def vault(self, vault_id):
        pass
