from ._vault import VaultController
from ._connections import Connection
from ._detect import Detect

# Public backward-compatible name -- existing consumers do `from skyflow.vault.controller import
# Vault`; VaultController is the canonical internal name (extends common.vault.base_vault_controller's
# BaseVaultController), but the old public name must keep resolving to the exact same class.
Vault = VaultController
