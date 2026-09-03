class ColumnRedaction:
    def __init__(self, column_name: str, redaction: str = None):
        self.column_name = column_name
        self.redaction = redaction
