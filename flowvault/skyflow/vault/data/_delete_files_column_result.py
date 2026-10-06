class DeleteFilesColumnResult:
    def __init__(self, column: str, status: str = None):
        self.column = column
        self.status = status

    def __repr__(self):
        return f"DeleteFilesColumnResult(column={self.column}, status={self.status})"

    def __str__(self):
        return self.__repr__()
