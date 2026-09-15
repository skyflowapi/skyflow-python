from typing import List

from ._bulk_insert_request_record import BulkInsertRequestRecord
from ._upsert_options import UpsertOptions


class BulkInsertRequest:
    def __init__(self, records: List[BulkInsertRequestRecord], table_name: str = None, upsert: UpsertOptions = None):
        self.records = records
        self.table_name = table_name
        self.upsert = upsert
