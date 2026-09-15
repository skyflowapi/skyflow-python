class BaseInsertResponse:

    def __init__(self, inserted_fields=None, errors=None):
        self.inserted_fields = inserted_fields
        self.errors = errors

    def __repr__(self):
        return f"{type(self).__name__}(inserted_fields={self.inserted_fields}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()
