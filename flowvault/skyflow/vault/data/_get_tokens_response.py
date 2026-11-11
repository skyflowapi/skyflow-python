from common.vault.data import BaseGetTokensResponse


class GetTokensResponse(BaseGetTokensResponse):
    def __init__(self, records=None):
        super().__init__(records)
