class TokenizeResponse:
    def __init__(self, records=None, errors=None):
        self.records = records
        self.errors = errors

    def __repr__(self):
        return f"TokenizeResponse(records={self.records}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()
