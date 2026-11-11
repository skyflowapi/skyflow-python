from typing import List


class DeleteFilesRequestRecord:
    def __init__(self, table_name: str, columns: List[str], skyflow_id: str = None, unique_values: List[dict] = None):
        self.table_name = table_name
        self.columns = columns
        self.skyflow_id = skyflow_id
        self.unique_values = unique_values
