class BulkDetokenizeResponseRecord:
    def __init__(self, token=None, value=None, token_group_name=None, metadata=None,
                 http_code=None, error=None, request_id=None, index=None):
        self.token = token
        self.value = value
        self.token_group_name = token_group_name
        self.metadata = metadata
        self.http_code = http_code
        self.error = error
        self.request_id = request_id
        self.index = index

    def __repr__(self):
        return ("BulkDetokenizeResponseRecord(index={}, token={}, value={}, token_group_name={}, "
                "metadata={}, http_code={}, error={}, request_id={})").format(
            self.index, self.token, self.value, self.token_group_name,
            self.metadata, self.http_code, self.error, self.request_id)
