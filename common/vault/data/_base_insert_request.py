class BaseInsertRequest:

    def __init__(self, table=None, records=None, upsert=None):
        self.table = table
        self.records = records
        self.upsert = upsert
