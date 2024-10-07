from skyflow.generated.rest import V1TokenizeResponse


class TokenizeResponse:
    def __init__(self, tokenized_fields):
        self.tokenized_fields = tokenized_fields


    def __repr__(self):
        return f"InsertResponse(tokenized_fields={self.tokenized_fields})"

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_tokenize_response(tokenize_response: V1TokenizeResponse):
        tokenized_fields = [{"token": record.token} for record in tokenize_response.records]

        return TokenizeResponse(
            tokenized_fields = tokenized_fields
        )