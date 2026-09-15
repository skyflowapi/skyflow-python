from skyflow.vault.detect._date_transformation import DateTransformation

class Transformations:
    def __init__(self, shift_dates: DateTransformation):
        self.shift_dates = shift_dates
