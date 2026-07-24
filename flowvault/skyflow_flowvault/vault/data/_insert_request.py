from common.vault.data import BaseInsertRequest
from skyflow_flowvault.vault.data._upsert import Upsert


class InsertRequest(BaseInsertRequest):
    def __init__(self, values: list, table: str = None, upsert: Upsert = None):
        super().__init__(table, values, upsert=upsert)
