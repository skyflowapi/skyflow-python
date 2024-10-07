class DetokenizeRequest:
    def __init__(self, tokens,redaction_type):
        self.tokens = tokens
        self.redaction_type = redaction_type
        self.continue_on_error = bool