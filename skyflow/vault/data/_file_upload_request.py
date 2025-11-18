from typing import BinaryIO

class FileUploadRequest:
    def __init__(self,
                 table: str,
                 skyflow_id: str,
                 column_name: str,
                 file_path: str= None,
                 base64: str= None,
                 file_object: BinaryIO= None,
                 file_name: str= None):
        self.table = table
        self.skyflow_id = skyflow_id
        self.column_name = column_name
        self.file_path = file_path
        self.base64 = base64
        self.file_object = file_object
        self.file_name = file_name
