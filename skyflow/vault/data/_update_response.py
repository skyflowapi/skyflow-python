from skyflow.generated.rest import V1UpdateRecordResponse

class UpdateResponse:
    def __init__(self, updated_field, error=None):
        self.updated_field = updated_field
        self.error = error if error is not None else []

    def __repr__(self):
        return f"UpdateResponse(updated_field={self.updated_field}, error={self.error})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_update_field_response(update_response: V1UpdateRecordResponse):
        updated_field = {}
        updated_field['skyflow_id'] = update_response.skyflow_id
        if update_response.tokens is not None:
            updated_field.update(update_response.tokens)

        return UpdateResponse(updated_field)
