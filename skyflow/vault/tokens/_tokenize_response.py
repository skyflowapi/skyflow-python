class TokenizeResponse:
    def __init__(self, tokenized_fields = None, errors = None):
        self.tokenized_fields = tokenized_fields
        self.errors = errors


    def __repr__(self):
        return f"TokenizeResponse(tokenized_fields={self.tokenized_fields}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()

