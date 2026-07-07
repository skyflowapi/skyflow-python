class InsertRecord:
    """One row to insert. table/upsert fall back to InsertRequest's values when unset here."""

    def __init__(self, data, table=None, upsert=None):
        self.data = data
        self.table = table
        self.upsert = upsert
