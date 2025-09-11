from io import BufferedReader

class FileInput:
    """
    Represents a file input for the vault detection process.
    
    Attributes:
        file (BufferedReader): The file object to be processed. This can be a file-like object or a binary string.
        file_path (str): The path to the file to be processed.
    """

    def __init__(self, file: BufferedReader= None, file_path: str = None):
        self.file = file
        self.file_path = file_path

    def __repr__(self) -> str:
        return f"FileInput(file={self.file!r}, file_path={self.file_path!r})"
    
    def __str__(self) -> str:
        return self.__repr__()
    