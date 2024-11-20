class GetResponse:
    def __init__(self, data=None, error = None):
        self.data = data if data else []
        self.error = error

    def __repr__(self):
        return f"GetResponse(data={self.data}, errors={self.error})"

    def __str__(self):
        return self.__repr__()