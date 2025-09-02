class FileUploadResponse:
    def __init__(self,
                 skyflow_id,
                 errors):
        self.skyflow_id = skyflow_id
        self.errors = errors
