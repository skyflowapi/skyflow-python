from skyflow.generated.rest import V1InsertRecordResponse, V1BatchOperationResponse


class InsertResponse:
    def __init__(self, inserted_fields = None, error_data = None):
        self.inserted_fields = inserted_fields
        self.error_data = error_data

    def __repr__(self):
        return f"InsertResponse(inserted_fields={self.inserted_fields}, error={self.error_data})"

    def __str__(self):
        return self.__repr__()
