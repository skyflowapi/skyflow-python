from typing import List
from skyflow.utils.enums.detect_entities import DetectEntities

class DateTransformation:
    def __init__(self, max_days: int, min_days: int, entities: List[DetectEntities]):
        self.max = max_days
        self.min = min_days
        self.entities = entities
