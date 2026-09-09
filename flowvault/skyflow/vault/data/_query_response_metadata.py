class QueryResponseMetadata:
    def __init__(self, columns=None):
        self.columns = columns

    def __repr__(self):
        return f"QueryResponseMetadata(columns={self.columns})"
