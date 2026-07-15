class DeleteRequest:
    def __init__(self, table: str, ids: list = None, unique_values: list = None):
        self.table = table
        self.ids = ids
        self.unique_values = unique_values
