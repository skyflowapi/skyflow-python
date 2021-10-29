class SkyflowConfiguration:
    def __init__(self, vaultID: str, vaultURL: str, tokenProvider):
        self.vaultID = vaultID
        self.vaultURL = vaultURL
        self.tokenProvider = tokenProvider

class InsertOptions:
    def __init__(self, tokens: bool=True):
        self.tokens = tokens