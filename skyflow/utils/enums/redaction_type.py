from enum import Enum

class RedactionType(Enum):
    PLAIN_TEXT = 'PLAIN_TEXT'
    MASKED = 'MASKED'
    DEFAULT = 'DEFAULT'
    REDACTED = 'REDACTED'
