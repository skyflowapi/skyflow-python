class InsertRequest:
    def __init__(self,
                 table_name,
                 values,
                 upsert = None,
                 homogeneous = False,
                 token_mode = None,
                 token_strict = None,
                 return_tokens= True,):
        self.table_name = table_name
        self.values = values
        self.upsert = upsert
        self.homogeneous = homogeneous
        self.token_mode = token_mode
        self.token_strict = token_strict
        self.return_tokens = return_tokens

