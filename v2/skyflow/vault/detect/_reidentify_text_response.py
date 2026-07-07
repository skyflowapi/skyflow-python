from typing import Optional

class ReidentifyTextResponse:
    def __init__(self, processed_text: str, errors: Optional[list] = None):
        self.processed_text = processed_text
        self.errors = errors

    def __repr__(self) -> str:
        return f"ReidentifyTextResponse(processed_text='{self.processed_text}', errors={self.errors})"

    def __str__(self) -> str:
        return self.__repr__()