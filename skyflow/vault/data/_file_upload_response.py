class FileUploadResponse:
    def __init__(self,
                 skyflow_id,
                 errors):
        self.skyflow_id = skyflow_id
        self.errors = errors
    
    def __repr__(self):
        return f"FileUploadResponse(skyflow_id={self.skyflow_id}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()