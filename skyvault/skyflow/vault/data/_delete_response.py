class DeleteResponse:
    def __init__(self, deleted_ids = None, errors = None):
        self.deleted_ids = deleted_ids
        self.errors = errors

    def __repr__(self):
        return f"DeleteResponse(deleted_ids={self.deleted_ids}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()

