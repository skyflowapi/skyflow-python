class DetokenizeRequest:
    def __init__(self, tokens: list, token_group_redactions: list = None):
        self.tokens = tokens
        self.token_group_redactions = token_group_redactions
