from typing import List

from common.vault.data import BaseDeleteFilesRequest
from ._delete_files_request_record import DeleteFilesRequestRecord


class DeleteFilesRequest(BaseDeleteFilesRequest):
    def __init__(self, records: List[DeleteFilesRequestRecord]):
        super().__init__(records)
