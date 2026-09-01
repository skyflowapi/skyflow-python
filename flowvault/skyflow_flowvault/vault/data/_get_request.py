from typing import List

from ._column_redaction import ColumnRedaction


class GetRequest:
    def __init__(self, table: str = None, ids: list = None, unique_values: list = None, columns: list = None,
                 column_redactions: List[ColumnRedaction] = None, limit: int = None, offset: int = None,
                 records: list = None):
        self.table = table
        self.ids = ids
        self.unique_values = unique_values
        self.columns = columns
        self.column_redactions = column_redactions
        self.limit = limit
        self.offset = offset
        self.records = records
