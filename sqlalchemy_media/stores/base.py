from typing import Union

from sqlalchemy_media.context import get_id as get_context_id
from sqlalchemy_media.helpers import open_stream
from sqlalchemy_media.stores.exceptions import ContextError
from sqlalchemy_media.typing import Stream


# Global variable to store contexts
context_stacks = {}


class Store(object):

    def put(self, filename: str, f: Union[str, Stream]):
        if isinstance(f, str):
            stream = open_stream(f)
        else:
            stream = f

        try:
            return self.put_stream(filename, stream)
        finally:
            if stream is not f:
                # This stream is opened by this method and should be closed, before leaving from.
                stream.close()

    # noinspection PyMethodMayBeStatic
    def cleanup(self):
        """
        Just do nothing here.
        """
        pass

    def put_stream(self, filename: str, stream: Stream):
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r') -> Stream:
        raise NotImplementedError()

    def __enter__(self):
        context_stacks.setdefault(get_context_id(), []).append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        context_stacks.setdefault(get_context_id(), []).pop()
        self.cleanup()

    @classmethod
    def get_current_store(cls) -> 'Store':
        try:
            return context_stacks.setdefault(get_context_id(), [])[-1]
        except IndexError:
            raise ContextError('not in store context.')
