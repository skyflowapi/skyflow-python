class UpdateRequest:
    def __init__(self, records: list, table_name: str = None, update_type=None):
        self.records = records
        self.table_name = table_name
        self.update_type = update_type
