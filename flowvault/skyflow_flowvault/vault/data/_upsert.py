class Upsert:
    """Mirrors the wire type V1Upsert. update_type is a skyflow_flowvault.utils.enums.UpsertType value."""

    def __init__(self, update_type=None, unique_columns=None):
        self.update_type = update_type
        self.unique_columns = unique_columns
