class DeidentifyFileResponse:
    def __init__(
        self,
        file: str = None,
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
        self.file = file
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

    def __repr__(self):
        return (
            f"DeidentifyFileResponse("
            f"file={self.file!r}, type={self.type!r}, extension={self.extension!r}, "
            f"word_count={self.word_count!r}, char_count={self.char_count!r}, "
            f"size_in_kb={self.size_in_kb!r}, duration_in_seconds={self.duration_in_seconds!r}, "
            f"page_count={self.page_count!r}, slide_count={self.slide_count!r}, "
            f"entities={self.entities!r}, run_id={self.run_id!r}, status={self.status!r}),"
            f"errors={self.errors!r})"
        )

    def __str__(self):
        return self.__repr__()