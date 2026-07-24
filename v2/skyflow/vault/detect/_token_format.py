from typing import List
from skyflow.utils.enums.detect_entities import DetectEntities
from skyflow.utils.enums.token_type import TokenType

class TokenFormat:
    def __init__(self, default: TokenType = TokenType.ENTITY_UNIQUE_COUNTER, 
                 vault_token: List[DetectEntities] = None,
                 entity_unique_counter: List[DetectEntities] = None,
                 entity_only: List[DetectEntities] = None):
        self.default = default
        self.vault_token = vault_token
        self.entity_unique_counter = entity_unique_counter
        self.entity_only = entity_only
