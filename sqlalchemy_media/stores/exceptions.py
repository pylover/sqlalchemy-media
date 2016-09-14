

class ContextError(Exception):
    pass


class DefaultStoreError(Exception):
    def __init__(self):
        super(DefaultStoreError, self).__init__("Default store is not defined.")
