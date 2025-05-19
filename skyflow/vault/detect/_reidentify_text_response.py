class ReidentifyTextResponse:
    def __init__(self, processed_text: str):
        self.processed_text = processed_text

    def __repr__(self) -> str:
        return f"ReidentifyTextResponse(processed_text='{self.processed_text}')"

    def __str__(self) -> str:
        return self.__repr__()