class UpdateResponse:
    def __init__(self, records=None):
        self.records = records

    def __repr__(self):
        return f"UpdateResponse(records={self.records})"

    def __str__(self):
        return self.__repr__()
