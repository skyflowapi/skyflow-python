from common.vault.data import BaseInsertRequest
from skyflow.utils.enums import TokenMode

class InsertRequest(BaseInsertRequest):
    def __init__(self,
                 table,
                 values,
                 tokens = None,
                 upsert = None,
                 homogeneous = False,
                 token_mode = TokenMode.DISABLE,
                 return_tokens = True,
                 continue_on_error = False):
        super().__init__(table, upsert=upsert)
        self.values = values
        self.tokens = tokens
        self.homogeneous = homogeneous
        self.token_mode = token_mode
        self.return_tokens = return_tokens
        self.continue_on_error = continue_on_error

