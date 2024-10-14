from skyflow.generated.rest import V1GetQueryResponse

class QueryResponse:
    def __init__(self, records):
        self.fields = []
        self.error = []

        for record in records:
            field_object = {
                **record.fields,
                "tokenizedData": {}
            }
            self.fields.append(field_object)

    def __repr__(self):
        return f"QueryResponse(fields={self.fields}, error={self.error})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_query_response(api_response: V1GetQueryResponse):
        return QueryResponse(api_response.records)