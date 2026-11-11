from typing import List

from common.vault.data import BaseUploadFilesRequest
from ._upload_files_request_record import UploadFilesRequestRecord


class UploadFilesRequest(BaseUploadFilesRequest):
    def __init__(self, records: List[UploadFilesRequestRecord]):
        super().__init__(records)
