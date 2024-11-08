from skyflow.utils.enums import TokenStrict

class InsertRequest:
    def __init__(self,
                 table_name,
                 values,
                 tokens = None,
                 upsert = None,
                 homogeneous = False,
                 token_strict = TokenStrict.DISABLE,
                 return_tokens = True,
                 continue_on_error = False):
        self.table_name = table_name
        self.values = values
        self.tokens = tokens
        self.upsert = upsert
        self.homogeneous = homogeneous
        self.token_strict = token_strict
        self.return_tokens = return_tokens
        self.continue_on_error = continue_on_error

