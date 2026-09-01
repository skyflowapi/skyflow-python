class DetokenizeResponse:
    def __init__(self, detokenized_fields = None, errors = None):
        self.detokenized_fields = detokenized_fields
        self.errors = errors

    def __repr__(self):
        return f"DetokenizeResponse(detokenized_fields={self.detokenized_fields}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()


