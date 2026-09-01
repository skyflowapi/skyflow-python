class DetokenizeRequest:
    def __init__(self, data, continue_on_error = False):
        self.data = data
        self.continue_on_error = continue_on_error