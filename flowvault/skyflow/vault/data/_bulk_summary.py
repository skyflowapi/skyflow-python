class BulkSummary:
    def __init__(self, total_records=0, total_inserted=0, total_failed=0):
        self.total_records = total_records
        self.total_inserted = total_inserted
        self.total_failed = total_failed

    def __repr__(self):
        return (f"BulkSummary(total_records={self.total_records}, "
                f"total_inserted={self.total_inserted}, total_failed={self.total_failed})")

    def __str__(self):
        return self.__repr__()
