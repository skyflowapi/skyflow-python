from enum import Enum


class UpsertType(Enum):
    """Mirrors the wire enum FlowEnumUpdateType (V1Upsert.update_type)."""
    REPLACE = "REPLACE"
    UPDATE = "UPDATE"
