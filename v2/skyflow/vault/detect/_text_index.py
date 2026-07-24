class TextIndex:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __repr__(self):
        return f"TextIndex(start={self.start}, end={self.end})"
        
    def __str__(self):
        return self.__repr__()
