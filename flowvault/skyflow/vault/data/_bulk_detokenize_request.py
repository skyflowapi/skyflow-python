from typing import List

from ._token_group_redactions import TokenGroupRedactions


class BulkDetokenizeRequest:
    def __init__(self, tokens: list, token_group_redactions: List[TokenGroupRedactions] = None):
        self.tokens = tokens
        self.token_group_redactions = token_group_redactions
