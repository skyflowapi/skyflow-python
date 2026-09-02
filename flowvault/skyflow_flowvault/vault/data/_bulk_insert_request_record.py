from ._upsert_options import UpsertOptions


class BulkInsertRequestRecord:
    def __init__(self, data: dict, table_name: str = None, tokens: dict = None, upsert: UpsertOptions = None):
        self.data = data
        self.table_name = table_name
        self.tokens = tokens
        self.upsert = upsert
