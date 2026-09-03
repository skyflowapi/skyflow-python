class UpsertOptions:
    def __init__(self, unique_columns: list = None, update_type=None):
        self.unique_columns = unique_columns
        self.update_type = update_type
