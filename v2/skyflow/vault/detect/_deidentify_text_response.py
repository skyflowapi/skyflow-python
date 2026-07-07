from typing import List, Optional
from ._entity_info import EntityInfo

class DeidentifyTextResponse:
    def __init__(self,
                processed_text: str,
                entities: List[EntityInfo],
                word_count: int,
                char_count: int,
                errors: Optional[list] = None):
        self.processed_text = processed_text
        self.entities = entities
        self.word_count = word_count
        self.char_count = char_count
        self.errors = errors

    def __repr__(self):
        return f"DeidentifyTextResponse(processed_text='{self.processed_text}', entities={self.entities}, word_count={self.word_count}, char_count={self.char_count}, errors={self.errors})"

    def __str__(self):
        return self.__repr__()