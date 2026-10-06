class GetTokensResponseRecord:
    def __init__(self, value=None, token_group_name=None, token=None,
                 http_code=None, error=None, request_id=None):
        self.value = value
        self.token_group_name = token_group_name
        self.token = token
        self.http_code = http_code
        self.error = error
        self.request_id = request_id

    def __repr__(self):
        return ("GetTokensResponseRecord(value={}, token_group_name={}, token={}, "
                "http_code={}, error={}, request_id={})").format(
            self.value, self.token_group_name, self.token,
            self.http_code, self.error, self.request_id)
