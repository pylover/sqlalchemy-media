

class ContextError(Exception):
    """
    The exception which rises when the :data:`current_store` is required
    but there's no currently set store context.

    """
    pass
