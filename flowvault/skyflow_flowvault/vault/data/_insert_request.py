from common.vault.data import BaseInsertRequest


class InsertRequest(BaseInsertRequest):
    """table/upsert are request-level defaults; individual InsertRecords may override either."""

    def __init__(self, records, table=None, upsert=None):
        super().__init__(table)
        self.records = records
        self.upsert = upsert
