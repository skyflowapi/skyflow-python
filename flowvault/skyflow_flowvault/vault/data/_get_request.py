class GetRequest:
    def __init__(self, table: str, ids: list = None, unique_values: list = None, columns: list = None,
                 column_redactions: list = None, limit: int = None, offset: int = None):
        self.table = table
        self.ids = ids
        self.unique_values = unique_values
        self.columns = columns
        self.column_redactions = column_redactions
        self.limit = limit
        self.offset = offset
