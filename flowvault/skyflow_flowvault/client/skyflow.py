from common.client.base_skyflow import make_skyflow_class
from common.utils import SkyflowMessages
from skyflow_flowvault.vault.client.client import VaultClient
from skyflow_flowvault.vault.controller import VaultController

Skyflow = make_skyflow_class(
    vault_client_cls=VaultClient,
    vault_controller_cls=VaultController,
    skyflow_messages=SkyflowMessages,
)
