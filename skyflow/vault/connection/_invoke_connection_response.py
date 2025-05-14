class InvokeConnectionResponse:
    def __init__(self, data=None, metadata=None):
        self.data = data
        self.metadata = metadata if metadata else {}

    def __repr__(self):
        return f"ConnectionResponse('data'={self.data},'metadata'={self.metadata})"

    def __str__(self):
        return self.__repr__()