class DeleteRequest:
    def __init__(self, table_name: str, ids: list = None, unique_values: list = None):
        self.table_name = table_name
        self.ids = ids
        self.unique_values = unique_values
