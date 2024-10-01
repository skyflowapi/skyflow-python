class GetRequest:
    def __init__(self, table, ids, redaction_type):
        self.table = table
        self.ids = ids
        self.redaction_type = redaction_type
