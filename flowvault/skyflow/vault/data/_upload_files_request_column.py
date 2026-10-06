from typing import BinaryIO


class UploadFilesRequestColumn:
    def __init__(self, column: str, file_path: str = None, base64: str = None,
                 file_object: BinaryIO = None, file_name: str = None, content_type: str = None):
        self.column = column
        self.file_path = file_path
        self.base64 = base64
        self.file_object = file_object
        self.file_name = file_name
        self.content_type = content_type
