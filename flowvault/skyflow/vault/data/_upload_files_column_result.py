class UploadFilesColumnResult:
    def __init__(self, column: str, file_name: str = None, upload_status: str = None, error: str = None):
        self.column = column
        self.file_name = file_name
        self.upload_status = upload_status
        self.error = error

    def __repr__(self):
        return ("UploadFilesColumnResult(column={}, file_name={}, upload_status={}, "
                "error={})").format(
            self.column, self.file_name, self.upload_status, self.error)
