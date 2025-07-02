class QueryResponse:
    def __init__(self):
        self.fields = []
        self.errors = None

    def __repr__(self):
        return f"QueryResponse(fields={self.fields}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()
