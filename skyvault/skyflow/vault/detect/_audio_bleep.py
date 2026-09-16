from typing import Optional

class Bleep:
    def __init__(
        self,
        gain: Optional[float] = None,
        frequency: Optional[float] = None,
        start_padding: Optional[float] = None,
        stop_padding: Optional[float] = None
    ):
        self.gain = gain
        self.frequency = frequency
        self.start_padding = start_padding
        self.stop_padding = stop_padding