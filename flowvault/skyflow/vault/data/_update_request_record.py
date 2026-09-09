class UpdateRequestRecord:
    def __init__(self, skyflow_id: str = None, data: dict = None, tokens: dict = None, table_name: str = None):
        self.skyflow_id = skyflow_id
        self.data = data
        self.tokens = tokens
        self.table_name = table_name
