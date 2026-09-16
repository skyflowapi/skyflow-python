from typing import List

from ._column_redactions import ColumnRedactions


class GetRequestRecord:
    def __init__(self, table_name: str, skyflow_ids: list = None, columns: list = None,
                 column_redactions: List[ColumnRedactions] = None, unique_values: list = None):
        self.table_name = table_name
        self.skyflow_ids = skyflow_ids
        self.columns = columns
        self.column_redactions = column_redactions
        self.unique_values = unique_values
