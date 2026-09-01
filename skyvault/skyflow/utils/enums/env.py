# Re-exports common's Env/EnvUrls rather than defining a separate duplicate class.
#
# Why this matters (found via a live run, not caught by tests): VaultClient.initialize_client_configuration()
# is inherited from common.vault.base_vault_client.BaseVaultClient, which calls common.utils.get_vault_url().
# That function validates its `env` argument with `if env not in Env` against *common's* Env class. If this
# module defined its own separate (even if identically-shaped) Env class, a value built from `skyflow.Env`
# would never satisfy that check -- plain Enum classes never compare equal across distinct class objects,
# even with matching member names/values. Re-exporting the same class object avoids that entirely.
#
# This is safe for v2 compatibility: values, names, and `.value`/`.name` behavior are unchanged --
# `skyflow.Env.PROD` still is `Env.PROD` with the same string value. Only the class's identity is now
# shared instead of duplicated, which is exactly what a config value needs to survive a round trip through
# shared validation code in common/.
from common.utils.enums import Env, EnvUrls

__all__ = ["Env", "EnvUrls"]
