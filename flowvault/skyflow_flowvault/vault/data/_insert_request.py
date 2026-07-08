from common.vault.data import BaseInsertRequest


class InsertRequest(BaseInsertRequest):
    """table/upsert are request-level defaults; individual records (plain dicts shaped
    {"values": {...}, "table": ..., "upsert": ...}) may override either."""

    def __init__(self, records, table=None, upsert=None):
        super().__init__(table, records=records, upsert=upsert)
