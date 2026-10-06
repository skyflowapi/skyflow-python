from enum import Enum


class FileUploadStatus(Enum):
    UPLOADED = "UPLOADED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
