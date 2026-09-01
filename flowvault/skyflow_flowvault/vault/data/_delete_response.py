class DeleteResponse:
    def __init__(self, records=None):
        self.records = records

    def __repr__(self):
        return f"DeleteResponse(records={self.records})"

    def __str__(self):
        return self.__repr__()
