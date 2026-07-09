from typing import Union

class BaseInsertRequest:
    def __init__(self, table: str, values: list, upsert: Union[str, dict] = None):
        self.table = table
        self.values = values
        self.upsert = upsert