class GetResponse:
    def __init__(self, data=None, errors = None):
        self.data = data if data else []
        self.errors = errors

    def __repr__(self):
        return f"GetResponse(data={self.data}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()