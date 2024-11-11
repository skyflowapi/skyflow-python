from skyflow.utils.enums import Redaction

class DetokenizeRequest:
    def __init__(self, tokens, redaction_type = "plain-text", continue_on_error = False):
        self.tokens = tokens
        self.redaction_type = Redaction.to_redaction_enum(redaction_type)
        self.continue_on_error = continue_on_error