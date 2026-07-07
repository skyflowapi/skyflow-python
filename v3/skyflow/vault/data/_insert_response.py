class InsertResponse:
    """summary/success/errors are all plain dicts (or lists of dicts) -- no custom classes.
    Each success/error entry is tagged with its index in the original records list."""

    def __init__(self, summary, success, errors):
        self.summary = summary
        self.success = success
        self.errors = errors

    def __repr__(self):
        return f"InsertResponse(summary={self.summary!r}, success={self.success!r}, errors={self.errors!r})"

    def __str__(self):
        return self.__repr__()
