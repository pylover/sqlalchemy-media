

class MaximumLengthIsReached(Exception):
    def __init__(self, max_length: int):
        super().__init__('Cannot store files smaller than: %d bytes' % max_length )


class MinimumLengthIsNotReached(Exception):
    def __init__(self, min_length):
        super().__init__('Cannot store files larger than: %d bytes' % min_length)
