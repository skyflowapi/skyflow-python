from skyflow.generated.rest import V1GetQueryResponse

class QueryResponse:
    def __init__(self):
        self.fields = []
        self.error = []

    def __repr__(self):
        return f"QueryResponse(fields={self.fields}, error={self.error})"

    def __str__(self):
        return self.__repr__()
