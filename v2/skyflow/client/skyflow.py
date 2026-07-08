from common.client.base_skyflow import make_skyflow_class
from skyflow.utils import SkyflowMessages
from skyflow.utils.logger import set_active_log_level
from skyflow.utils.validations import validate_connection_config, validate_update_connection_config
from skyflow.vault.client.client import VaultClient
from skyflow.vault.controller import VaultController, Connection, Detect

Skyflow = make_skyflow_class(
    vault_client_cls=VaultClient,
    vault_controller_cls=VaultController,
    connection_cls=Connection,
    detect_cls=Detect,
    skyflow_messages=SkyflowMessages,
    validate_connection_config=validate_connection_config,
    validate_update_connection_config=validate_update_connection_config,
    set_active_log_level=set_active_log_level,
)
