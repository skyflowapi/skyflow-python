from enum import Enum


class DeidentifySourceType(Enum):
    BASE64 = "BASE64"
    PRESIGNED_URL = "PRESIGNED_URL"
