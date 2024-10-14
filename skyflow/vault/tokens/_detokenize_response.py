from skyflow.generated.rest import V1DetokenizeResponse

class DetokenizeResponse:
    def __init__(self, detokenized_fields, errors):
        self.detokenized_fields = detokenized_fields
        self.errors = errors

    def __repr__(self):
        return f"DetokenizeResponse(detokenized_fields={self.detokenized_fields}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_detokenize_response(v1_detokenize_response: V1DetokenizeResponse):

        detokenized_fields = []
        errors = []

        for record in v1_detokenize_response.records:
            if record.error:
                errors.append({
                    "token": record.token,
                    "error": record.error
                })
            else:
                value_type = record.value_type.value if record.value_type else None
                detokenized_fields.append({
                    "token": record.token,
                    "value": record.value,
                    "type": value_type
                })

        return DetokenizeResponse(
            detokenized_fields=detokenized_fields,
            errors=errors
        )
