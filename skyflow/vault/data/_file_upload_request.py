import warnings
from typing import BinaryIO, Optional

from skyflow.utils import SkyflowMessages


class FileUploadRequest:
    def __init__(self,
                 table: str,
                 *args,
                 column_name: Optional[str] = None,
                 skyflow_id: Optional[str] = None,
                 file_path: Optional[str] = None,
                 base64: Optional[str] = None,
                 file_object: Optional[BinaryIO] = None,
                 file_name: Optional[str] = None):
        if args:
            warnings.warn(
                SkyflowMessages.Warning.FILE_UPLOAD_REQUEST_ARG_ORDER_DEPRECATED.value,
                DeprecationWarning,
                stacklevel=2,
            )
            # Old positional order was: (table, skyflow_id, column_name, ...)
            skyflow_id = args[0] if args else skyflow_id
            column_name = args[1] if len(args) > 1 else column_name
        self.table = table
        self.skyflow_id = skyflow_id
        self.column_name = column_name
        self.file_path = file_path
        self.base64 = base64
        self.file_object = file_object
        self.file_name = file_name
