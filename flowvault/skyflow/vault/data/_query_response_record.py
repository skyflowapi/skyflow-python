class QueryResponseRecord:
    def __init__(self, data=None):
        self.data = data

    def __repr__(self):
        return f"QueryResponseRecord(data={self.data})"
