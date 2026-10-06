from common.vault.data import BaseQueryResponse


class QueryResponse(BaseQueryResponse):
    def __init__(self, records=None, metadata=None, request_id=None):
        super().__init__(records)
        self.metadata = metadata
        self.request_id = request_id

    def __repr__(self):
        return f"QueryResponse(records={self.records}, metadata={self.metadata}, request_id={self.request_id})"

    def __str__(self):
        return self.__repr__()
