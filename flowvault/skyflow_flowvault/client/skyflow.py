from common.client.utils import make_skyflow_class
from common.utils import SkyflowMessages
from skyflow_flowvault.client._http_config_builder import HttpConfigBuilderMixin
from skyflow_flowvault.utils.validations import validate_vault_config, validate_update_vault_config
from skyflow_flowvault.vault.client.client import VaultClient
from skyflow_flowvault.vault.controller import VaultController

Skyflow = make_skyflow_class(
    vault_client_cls=VaultClient,
    vault_controller_cls=VaultController,
    skyflow_messages=SkyflowMessages,
    validate_vault_config=validate_vault_config,
    validate_update_vault_config=validate_update_vault_config,
    builder_mixins=(HttpConfigBuilderMixin,),
)
