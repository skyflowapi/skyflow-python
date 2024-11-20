from enum import Enum
from skyflow.generated.rest import RedactionEnumREDACTION

class RedactionType(Enum):
    PLAIN_TEXT = RedactionEnumREDACTION.PLAIN_TEXT
    MASKED = RedactionEnumREDACTION.MASKED
    DEFAULT = RedactionEnumREDACTION.DEFAULT
    REDACTED = RedactionEnumREDACTION.REDACTED
