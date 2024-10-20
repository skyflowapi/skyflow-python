class InvokeConnectionResponse:
    def __init__(self, response = None):
        self.response = response

    def __repr__(self):
        return f"ConnectionResponse({self.response})"

    def __str__(self):
        return self.__repr__()

    def parse_invoke_connection_response(self, response):
        self.response = response