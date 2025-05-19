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

    def __repr__(self) -> str:
        return (f"EntityInfo(token='{self.token}', value='{self.value}', "
                f"text_index={self.text_index}, processed_index={self.processed_index}, "
                f"entity='{self.entity}', scores={self.scores})")

    def __str__(self) -> str:
        return self.__repr__()