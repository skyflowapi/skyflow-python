class UpdateResponse:
    def __init__(self, updated_field = None, errors=None):
        self.updated_field = updated_field
        self.errors = errors

    def __repr__(self):
        return f"UpdateResponse(updated_field={self.updated_field}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()
