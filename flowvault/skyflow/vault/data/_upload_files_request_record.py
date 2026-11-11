from typing import List

from ._upload_files_request_column import UploadFilesRequestColumn


class UploadFilesRequestRecord:
    def __init__(self, table_name: str, columns: List[UploadFilesRequestColumn], skyflow_id: str = None):
        self.table_name = table_name
        self.columns = columns
        self.skyflow_id = skyflow_id
