from common.vault.data import BaseDeleteFilesResponse


class DeleteFilesResponse(BaseDeleteFilesResponse):
    def __init__(self, records=None):
        super().__init__(records)
