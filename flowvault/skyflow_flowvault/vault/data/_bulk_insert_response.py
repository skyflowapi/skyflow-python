MIN_RETRYABLE_HTTP_CODE = 500
MAX_RETRYABLE_HTTP_CODE = 599
NON_RETRYABLE_HTTP_CODE = 529


def _is_retryable(http_code):
    return (
        isinstance(http_code, int)
        and MIN_RETRYABLE_HTTP_CODE <= http_code <= MAX_RETRYABLE_HTTP_CODE
        and http_code != NON_RETRYABLE_HTTP_CODE
    )


class BulkInsertResponse:
    def __init__(self, summary=None, records=None, _original_records=None):
        self.summary = summary
        self.records = records
        self._original_records = _original_records

    def records_to_retry(self):
        if not self._original_records:
            return []
        return [
            self._original_records[record["index"]]
            for record in (self.records or [])
            if _is_retryable(record.get("http_code")) and 0 <= record.get("index", -1) < len(self._original_records)
        ]

    def __repr__(self):
        return f"BulkInsertResponse(summary={self.summary}, records={self.records})"

    def __str__(self):
        return self.__repr__()
