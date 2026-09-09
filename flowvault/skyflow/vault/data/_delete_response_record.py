class DeleteResponseRecord:
    def __init__(self, skyflow_id=None, http_code=None, error=None, request_id=None):
        self.skyflow_id = skyflow_id
        self.http_code = http_code
        self.error = error
        self.request_id = request_id

    def __repr__(self):
        return f"DeleteResponseRecord(skyflow_id={self.skyflow_id}, http_code={self.http_code}, error={self.error}, request_id={self.request_id})"
