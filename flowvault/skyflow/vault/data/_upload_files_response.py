from common.vault.data import BaseUploadFilesResponse


class UploadFilesResponse(BaseUploadFilesResponse):
    def __init__(self, records=None):
        super().__init__(records)
