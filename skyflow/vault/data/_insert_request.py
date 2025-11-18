from skyflow.utils.enums import TokenMode

class InsertRequest:
    def __init__(self,
                 table,
                 values,
                 tokens = None,
                 upsert = None,
                 homogeneous = False,
                 token_mode = TokenMode.DISABLE,
                 return_tokens = True,
                 continue_on_error = False):
        self.table = table
        self.values = values
        self.tokens = tokens
        self.upsert = upsert
        self.homogeneous = homogeneous
        self.token_mode = token_mode
        self.return_tokens = return_tokens
        self.continue_on_error = continue_on_error

