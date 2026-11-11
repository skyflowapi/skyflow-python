class QueryResponseMetadata:
    def __init__(self, columns: list = None):
        self.columns = columns

    def __repr__(self):
        return f"QueryResponseMetadata(columns={self.columns})"

    def __str__(self):
        return self.__repr__()
