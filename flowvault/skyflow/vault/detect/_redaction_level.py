from common.vault.detect import RedactionRule


class RedactionLevel(RedactionRule):
    def __init__(self, token_group_name: str = None,
                 redaction_pattern: str = None):
        self.token_group_name = token_group_name
        self.redaction_pattern = redaction_pattern

    def _api_token_group_name(self):
        return self.token_group_name

    def _api_redaction_pattern(self):
        return self.redaction_pattern
