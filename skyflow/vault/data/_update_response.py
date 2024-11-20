class UpdateResponse:
    def __init__(self, updated_field = None, error=None):
        self.updated_field = updated_field
        self.error = error if error is not None else []

    def __repr__(self):
        return f"UpdateResponse(updated_field={self.updated_field}, errors={self.error})"

    def __str__(self):
        return self.__repr__()
