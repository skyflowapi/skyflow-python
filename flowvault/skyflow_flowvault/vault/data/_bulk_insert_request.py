from typing import List

from ._bulk_insert_record import BulkInsertRecord
from ._upsert_options import UpsertOptions


class BulkInsertRequest:
    def __init__(self, records: List[BulkInsertRecord], table: str = None, upsert: UpsertOptions = None):
        self.records = records
        self.table = table
        self.upsert = upsert
