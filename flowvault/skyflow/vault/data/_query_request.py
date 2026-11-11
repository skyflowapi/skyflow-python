from common.vault.data import BaseQueryRequest


class QueryRequest(BaseQueryRequest):
    def __init__(self, query: str):
        super().__init__(query)
