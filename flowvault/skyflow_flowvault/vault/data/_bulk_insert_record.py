from ._upsert_options import UpsertOptions


class BulkInsertRecord:
    def __init__(self, data: dict, table: str = None, upsert: UpsertOptions = None):
        self.data = data
        self.table = table
        self.upsert = upsert
