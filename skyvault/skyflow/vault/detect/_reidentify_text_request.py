from typing import List, Optional
from skyflow.utils.enums.detect_entities import DetectEntities

class ReidentifyTextRequest:
    def __init__(self, text: str,
                redacted_entities: Optional[List[DetectEntities]] = None,
                masked_entities: Optional[List[DetectEntities]] = None,
                plain_text_entities: Optional[List[DetectEntities]] = None):
        self.text = text
        self.redacted_entities = redacted_entities
        self.masked_entities = masked_entities
        self.plain_text_entities = plain_text_entities
