from skyflow.generated.rest import V1BulkGetRecordResponse


class GetResponse:
    def __init__(self, data=None, error = []):
        self.data = data if data else []
        self.error = error

    def __repr__(self):
        return f"GetResponse(data={self.data}, error={self.error})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parsed_get_response(get_response: V1BulkGetRecordResponse):
        data = []
        error=[]
        for record in get_response.records:
            field_data = {field: value for field, value in record.fields.items()}
            data.append(field_data)

        return GetResponse(data, error=error)