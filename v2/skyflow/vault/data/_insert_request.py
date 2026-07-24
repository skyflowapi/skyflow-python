from common.vault.data import BaseInsertRequest
from skyflow.utils.enums import TokenMode

class InsertRequest(BaseInsertRequest):
    def __init__(self,
                 table: str,
                 values: list,
                 tokens: list = None,
                 upsert: str = None,
                 homogeneous: bool = False,
                 token_mode: TokenMode = TokenMode.DISABLE,
                 return_tokens: bool = True,
                 continue_on_error: bool = False):
        super().__init__(table, values, upsert=upsert)
        self.tokens = tokens
        self.homogeneous = homogeneous
        self.token_mode = token_mode
        self.return_tokens = return_tokens
        self.continue_on_error = continue_on_error

