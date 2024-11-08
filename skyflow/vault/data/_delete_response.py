class DeleteResponse:
    def __init__(self, deleted_ids = None, error = None):
        self.deleted_ids = deleted_ids
        self.error = error

    def __repr__(self):
        return f"DeleteResponse(deleted_ids={self.deleted_ids}, error={self.error})"

    def __str__(self):
        return self.__repr__()

