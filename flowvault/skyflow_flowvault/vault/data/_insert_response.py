from common.vault.data import BaseInsertResponse


class InsertResponse(BaseInsertResponse):
    """flowvault's own insert() response class -- currently identical to the shared base, kept as
    its own subclass so flowvault-specific fields can be added later without touching PDB."""
