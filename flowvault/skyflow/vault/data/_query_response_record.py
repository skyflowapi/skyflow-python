class QueryResponseRecord:
    def __init__(self, data: dict = None):
        self.data = data

    def __repr__(self):
        return f"QueryResponseRecord(data={self.data})"

    def __str__(self):
        return self.__repr__()
