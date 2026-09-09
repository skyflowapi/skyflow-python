class BulkInsertResponseRecord:
    def __init__(self, skyflow_id=None, table_name=None, tokens=None, data=None,
                 hashed_data=None, http_code=None, error=None, request_id=None, index=None):
        self.skyflow_id = skyflow_id
        self.table_name = table_name
        self.tokens = tokens
        self.data = data
        self.hashed_data = hashed_data
        self.http_code = http_code
        self.error = error
        self.request_id = request_id
        self.index = index

    def __repr__(self):
        return ("BulkInsertResponseRecord(index={}, skyflow_id={}, table_name={}, tokens={}, data={}, "
                "hashed_data={}, http_code={}, error={}, request_id={})").format(
            self.index, self.skyflow_id, self.table_name, self.tokens, self.data,
            self.hashed_data, self.http_code, self.error, self.request_id)
