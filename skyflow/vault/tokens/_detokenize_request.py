from skyflow.utils.enums.redaction_type import RedactionType

class DetokenizeRequest:
    def __init__(self, tokens, redaction_type = RedactionType.PLAIN_TEXT, continue_on_error = False):
        self.tokens = tokens
        self.redaction_type = redaction_type
        self.continue_on_error = continue_on_error