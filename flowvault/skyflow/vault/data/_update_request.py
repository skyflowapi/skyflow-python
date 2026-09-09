from typing import List

from skyflow.utils.enums import UpsertType
from ._update_request_record import UpdateRequestRecord


class UpdateRequest:
    def __init__(self, records: List[UpdateRequestRecord], table_name: str = None, update_type: UpsertType = None):
        self.records = records
        self.table_name = table_name
        self.update_type = update_type
