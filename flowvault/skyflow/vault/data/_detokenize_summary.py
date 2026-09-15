class DetokenizeSummary:
    def __init__(self, total_tokens=0, total_detokenized=0, total_failed=0):
        self.total_tokens = total_tokens
        self.total_detokenized = total_detokenized
        self.total_failed = total_failed

    def __repr__(self):
        return (f"DetokenizeSummary(total_tokens={self.total_tokens}, "
                f"total_detokenized={self.total_detokenized}, total_failed={self.total_failed})")

    def __str__(self):
        return self.__repr__()
