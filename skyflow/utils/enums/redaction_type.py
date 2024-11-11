from skyflow.generated.rest import RedactionEnumREDACTION


class Redaction:
    @staticmethod
    def to_redaction_enum(value):
        if value == "plain-text":
            return RedactionEnumREDACTION.PLAIN_TEXT
        elif value == "masked":
            return RedactionEnumREDACTION.MASKED
        elif value == "default":
            return RedactionEnumREDACTION.DEFAULT
        elif value == "redacted":
            return RedactionEnumREDACTION.REDACTED
