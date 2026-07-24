class InvokeConnectionResponse:
    def __init__(self, data=None, metadata=None, errors=None):
        self.data = data
        self.metadata = metadata if metadata else {}
        self.errors = errors if errors else None

    def __repr__(self):
        return f"ConnectionResponse('data'={self.data},'metadata'={self.metadata}), 'errors'={self.errors})"

    def __str__(self):
        return self.__repr__()