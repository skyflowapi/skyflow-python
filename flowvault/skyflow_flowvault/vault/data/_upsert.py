from typing import Optional, TypedDict
from skyflow_flowvault.utils.enums import UpsertType

class Upsert(TypedDict, total=False):
    update_type: Optional[UpsertType]
    unique_columns: list
