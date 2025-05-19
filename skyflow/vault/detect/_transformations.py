from skyflow.vault.detect._date_transformation import DateTransformation

class Transformations:
    def __init__(self, shift_days: DateTransformation):
        self.shift_days = shift_days
