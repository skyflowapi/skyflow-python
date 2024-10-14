class InvokeConnectionResponse:
    def __init__(self, fields, error):
        self.fields = fields
        self.error = error

    def __repr__(self):
        return f"ConnectionResponse({self.fields}, errors={self.error})"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def parse_invoke_connection_response(cls, response):
        return response