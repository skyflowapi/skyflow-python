from dataclasses import dataclass
from typing import List, Dict
from ._text_index import TextIndex
from ._entity_info import EntityInfo

@dataclass
class DeidentifyTextResponse:
    processed_text: str
    entities: List[EntityInfo]
    word_count: int
    char_count: int

    @property
    def processed_text(self) -> str:
        return self._processed_text

    @processed_text.setter
    def processed_text(self, value: str):
        self._processed_text = value

    @property
    def entities(self) -> List[EntityInfo]:
        return self._entities

    @entities.setter
    def entities(self, value: List[EntityInfo]):
        self._entities = value

    @property
    def word_count(self) -> int:
        return self._word_count

    @word_count.setter
    def word_count(self, value: int):
        self._word_count = value

    @property
    def char_count(self) -> int:
        return self._char_count

    @char_count.setter
    def char_count(self, value: int):
        self._char_count = value

    def __init__(self, processed_text: str, entities: List[EntityInfo], 
                 word_count: int, char_count: int):
        self._processed_text = processed_text
        self._entities = entities
        self._word_count = word_count
        self._char_count = char_count
