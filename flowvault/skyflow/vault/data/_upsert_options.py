from skyflow.utils.enums import UpsertType


class UpsertOptions:
    def __init__(self, unique_columns: list = None, update_type: UpsertType = None):
        self.unique_columns = unique_columns
        self.update_type = update_type
