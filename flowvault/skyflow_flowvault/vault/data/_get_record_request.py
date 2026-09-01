from typing import List

from ._column_redaction import ColumnRedaction


class GetRecordRequest:
    def __init__(self, table: str, ids: list = None, columns: list = None,
                 column_redactions: List[ColumnRedaction] = None, unique_values: list = None):
        self.table = table
        self.ids = ids
        self.columns = columns
        self.column_redactions = column_redactions
        self.unique_values = unique_values
