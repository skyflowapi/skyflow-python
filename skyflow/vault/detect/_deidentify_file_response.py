import io
from skyflow.vault.detect._file import File

class DeidentifyFileResponse:
    def __init__(
        self,
        file_base64: str = None,
        file: io.BytesIO = None,
        type: str = None,
        extension: str = None,
        word_count: int = None,
        char_count: int = None,
        size_in_kb: float = None,
        duration_in_seconds: float = None,
        page_count: int = None,
        slide_count: int = None,
        entities: list = None,  # list of dicts with keys 'file' and 'extension'
        run_id: str = None,
        status: str = None,
    ):
        self.file_base64 = file_base64
        self.file = File(file) if file else None
        self.type = type
        self.extension = extension
        self.word_count = word_count
        self.char_count = char_count
        self.size_in_kb = size_in_kb
        self.duration_in_seconds = duration_in_seconds
        self.page_count = page_count
        self.slide_count = slide_count
        self.entities = entities if entities is not None else []
        self.run_id = run_id
        self.status = status

    def __repr__(self):
        return (
            f"DeidentifyFileResponse("
            f"file_base64={self.file_base64!r}, file={self.file!r}, type={self.type!r}, "
            f"extension={self.extension!r}, word_count={self.word_count!r}, "
            f"char_count={self.char_count!r}, size_in_kb={self.size_in_kb!r}, "
            f"duration_in_seconds={self.duration_in_seconds!r}, page_count={self.page_count!r}, "
            f"slide_count={self.slide_count!r}, entities={self.entities!r}, "
            f"run_id={self.run_id!r}, status={self.status!r})"
        )

    def __str__(self):
        return self.__repr__()