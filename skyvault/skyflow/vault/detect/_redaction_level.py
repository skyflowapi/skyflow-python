from common.vault.detect import RedactionRule


class RedactionLevel(RedactionRule):
    def __init__(self, entity_name: "EntityType" = None,
                 redaction_type: "RedactionType" = None):
        self.entity_name = entity_name
        self.redaction_type = redaction_type

    def _api_entity_name(self):
        return self.entity_name

    def _api_redaction_type(self):
        return self.redaction_type
