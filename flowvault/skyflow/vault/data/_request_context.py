NOT_BATCHED = -1


class RequestContext:
    def __init__(self, operation, batch_index=NOT_BATCHED, total_batches=NOT_BATCHED):
        self.operation = operation
        self.batch_index = batch_index
        self.total_batches = total_batches
        self._headers = {}

    def add_header(self, key, value):
        self._headers[key] = value

    @property
    def headers(self):
        return dict(self._headers)
