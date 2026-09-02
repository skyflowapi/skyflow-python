from typing import List

from ._insert_request_record import InsertRequestRecord
from ._upsert_options import UpsertOptions


class InsertRequest:
    def __init__(self, records: List[InsertRequestRecord], table_name: str = None, upsert: UpsertOptions = None):
        self.records = records
        self.table_name = table_name
        self.upsert = upsert
