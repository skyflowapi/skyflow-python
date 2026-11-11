class BaseUploadFilesResponse:
    def __init__(self, records=None):
        self.records = records

    def __repr__(self):
        return f"{type(self).__name__}(records={self.records})"

    def __str__(self):
        return self.__repr__()
