class DeleteFilesResponseRecord:
    def __init__(self, skyflow_id: str = None, table_name: str = None, columns=None,
                 http_code: int = None, error: str = None, request_id: str = None):
        self.skyflow_id = skyflow_id
        self.table_name = table_name
        self.columns = columns
        self.http_code = http_code
        self.error = error
        self.request_id = request_id

    def __repr__(self):
        return ("DeleteFilesResponseRecord(skyflow_id={}, table_name={}, columns={}, "
                "http_code={}, error={}, request_id={})").format(
            self.skyflow_id, self.table_name, self.columns,
            self.http_code, self.error, self.request_id)
