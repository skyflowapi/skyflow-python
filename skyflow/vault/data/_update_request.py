from skyflow.utils.enums import TokenStrict


class UpdateRequest:
    def __init__(self, table, data, tokens = None, return_tokens = False, token_strict = TokenStrict.DISABLE):
        self.table = table
        self.data = data
        self.tokens = tokens
        self.return_tokens = return_tokens
        self.token_strict = token_strict
