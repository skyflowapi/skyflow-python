import io
import mimetypes
import time

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
        errors: list = [],
    ):
        self.file_base64 = file_base64
        self.file = file
        self.file_info = self._extract_file_info(file) if file else None
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
        self.errors = errors
    
    def _extract_file_info(self, file: io.BytesIO) -> dict:
        try:
            pos = file.tell()
            file.seek(0, io.SEEK_END)
            size = file.tell()
            file.seek(pos)
            name = getattr(file, 'name', 'unknown')
            file_type = mimetypes.guess_type(name)[0] or ''
            last_modified = int(time.time() * 1000)

            return {
                "name": name,
                "size": size,
                "type": file_type,
                "last_modified": last_modified
            }
        except Exception as e:
            return {
                "error": str(e)
            }

    def get_file_info(self) -> dict:
        """Public method to get file metadata"""
        return self.file_info

    def __repr__(self):
        return (
            f"DeidentifyFileResponse("
            f"file_base64={self.file_base64!r}, file={self.file_info}, type={self.type!r}, "
            f"extension={self.extension!r}, word_count={self.word_count!r}, "
            f"char_count={self.char_count!r}, size_in_kb={self.size_in_kb!r}, "
            f"duration_in_seconds={self.duration_in_seconds!r}, page_count={self.page_count!r}, "
            f"slide_count={self.slide_count!r}, entities={self.entities!r}, "
            f"run_id={self.run_id!r}, status={self.status!r}, errors={self.errors!r})"
        )

    def __str__(self):
        return self.__repr__()