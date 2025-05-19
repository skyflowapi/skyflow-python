from typing import Dict
from ._text_index import TextIndex

class EntityInfo:
    def __init__(self, token: str, value: str, text_index: TextIndex, 
                 processed_index: TextIndex, entity: str, scores: Dict[str, float]):
        self.token = token
        self.value = value
        self.text_index = text_index
        self.processed_index = processed_index
        self.entity = entity
        self.scores = scores
