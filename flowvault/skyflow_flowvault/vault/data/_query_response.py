class QueryResponse:
    def __init__(self, records=None, metadata=None):
        self.records = records
        self.metadata = metadata

    def __repr__(self):
        return f"QueryResponse(records={self.records}, metadata={self.metadata})"

    def __str__(self):
        return self.__repr__()
