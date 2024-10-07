class UpdateRequest:
    def __init__(self, table, data, return_tokens):
        self.table = table
        self.data = data
        self.return_tokens = return_tokens