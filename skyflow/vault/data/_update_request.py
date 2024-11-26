from skyflow.utils.enums import TokenMode

class UpdateRequest:
    def __init__(self, table, data, tokens = None, return_tokens = False, token_mode = TokenMode.DISABLE):
        self.table = table
        self.data = data
        self.tokens = tokens
        self.return_tokens = return_tokens
        self.token_mode = token_mode
