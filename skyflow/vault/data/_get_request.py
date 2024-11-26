class GetRequest:
    def __init__(self,
                 table,
                 ids = None,
                 redaction_type = None,
                 return_tokens = False,
                 fields = None,
                 offset  = None,
                 limit = None,
                 download_url = None,
                 column_name = None,
                 column_values = None):
        self.table = table
        self.ids = ids
        self.redaction_type = redaction_type
        self.return_tokens = return_tokens
        self.fields = fields
        self.offset = offset
        self.limit = limit
        self.download_url = download_url
        self.column_name = column_name
        self.column_values = column_values