from skyflow.generated.rest import V1BulkGetRecordResponse


class GetResponse:
    def __init__(self, data=None, error = None):
        self.data = data if data else []
        self.error = error

    def __repr__(self):
        return f"GetResponse(data={self.data}, error={self.error})"

    def __str__(self):
        return self.__repr__()