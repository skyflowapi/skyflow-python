class UpdateRequest:
    def __init__(self, records: list, table: str = None, update_type=None):
        self.records = records
        self.table = table
        self.update_type = update_type
