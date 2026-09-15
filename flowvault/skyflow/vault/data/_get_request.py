from typing import List

from ._column_redactions import ColumnRedactions


class GetRequest:
    def __init__(self, table_name: str = None, skyflow_ids: list = None, unique_values: list = None, columns: list = None,
                 column_redactions: List[ColumnRedactions] = None, limit: int = None, offset: int = None,
                 records: list = None):
        self.table_name = table_name
        self.skyflow_ids = skyflow_ids
        self.unique_values = unique_values
        self.columns = columns
        self.column_redactions = column_redactions
        self.limit = limit
        self.offset = offset
        self.records = records
