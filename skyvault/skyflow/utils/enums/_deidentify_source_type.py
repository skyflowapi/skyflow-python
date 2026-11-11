from enum import Enum


class DeidentifySourceType(Enum):
    BASE64 = "BASE64"
    SKYFLOW_ID = "SKYFLOW_ID"
    PRESIGNED_URL = "PRESIGNED_URL"
