class InsertResponse:
    def __init__(self, inserted_fields = None, error_data=None):
        if error_data is None:
            error_data = list()
        self.inserted_fields = inserted_fields
        self.error_data = error_data

    def __repr__(self):
        return f"InsertResponse(inserted_fields={self.inserted_fields}, errors={self.error_data})"

    def __str__(self):
        return self.__repr__()
