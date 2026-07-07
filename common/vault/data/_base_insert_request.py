class BaseInsertRequest:
    """Thin shared base for variant InsertRequest classes, mirrors skyflow-java's."""

    def __init__(self, table=None):
        self.table = table
