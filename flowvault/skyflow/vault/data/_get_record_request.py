from typing import List

from ._column_redactions import ColumnRedactions


class GetRecordRequest:
    def __init__(self, table_name: str, ids: list = None, columns: list = None,
                 column_redactions: List[ColumnRedactions] = None, unique_values: list = None):
        self.table_name = table_name
        self.ids = ids
        self.columns = columns
        self.column_redactions = column_redactions
        self.unique_values = unique_values
