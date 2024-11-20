class TokenizeResponse:
    def __init__(self, tokenized_fields = None):
        self.tokenized_fields = tokenized_fields


    def __repr__(self):
        return f"TokenizeResponse(tokenized_fields={self.tokenized_fields})"

    def __str__(self):
        return self.__repr__()

