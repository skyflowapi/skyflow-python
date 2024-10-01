class VaultManager:
    def __init__(self, vault_client, vault_controller):
        self.__vault_client = vault_client
        self.__controller = vault_controller

    def get_vault_client(self):
        return self.__vault_client

    def get_vault_controller(self):
        return self.__controller
