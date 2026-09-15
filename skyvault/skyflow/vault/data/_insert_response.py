from common.vault.data import BaseInsertResponse


class InsertResponse(BaseInsertResponse):
    """PDB's own insert() response class -- currently identical to the shared base, kept as its
    own subclass so PDB-specific fields can be added later without touching flowvault."""
