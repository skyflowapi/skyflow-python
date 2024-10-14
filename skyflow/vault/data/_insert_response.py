from skyflow.generated.rest import V1InsertRecordResponse


class InsertResponse:
    def __init__(self, inserted_fields, error_data = None):
        self.inserted_fields = inserted_fields
        self.error_data = error_data

    def __repr__(self):
        return f"InsertResponse(inserted_fields={self.inserted_fields}, error={self.error_data})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_insert_response(response: V1InsertRecordResponse):
        inserted_fields = []

        if response.records:
            for record in response.records:

                record_data = dict()
                record_data["skyflow_id"] = record.skyflow_id

                if record.tokens:
                    for field_name, token in record.tokens.items():
                        record_data[field_name] = token

                inserted_fields.append(record_data)

        insert_response = InsertResponse(
            inserted_fields = inserted_fields,
            error_data=[]
        )

        return insert_response
