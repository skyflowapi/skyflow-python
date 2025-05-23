from typing import List, Optional
from skyflow.utils.enums.detect_entities import DetectEntities
from ._token_format import TokenFormat
from ._transformations import Transformations

class DeidentifyTextRequest:
    def __init__(self, 
                 text: str, 
                 entities: Optional[List[DetectEntities]] = None,
                 allow_regex_list: Optional[List[str]] = None,
                 restrict_regex_list: Optional[List[str]] = None,
                 token_format: Optional[TokenFormat] = None,
                 transformations: Optional[Transformations] = None):
        self.text = text
        self.entities = entities
        self.allow_regex_list = allow_regex_list
        self.restrict_regex_list = restrict_regex_list
        self.token_format = token_format
        self.transformations = transformations
