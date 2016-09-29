from typing import Union

from sqlalchemy_media.helpers import open_stream
from sqlalchemy_media.typing import Stream


class Store(object):

    def put(self, filename: str, f: Union[str, Stream], *, min_length=None, max_length=None):
        if isinstance(f, str):
            stream = open_stream(f)
        else:
            stream = f

        try:
            return self.put_stream(filename, stream, min_length=min_length, max_length=max_length)
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

    def put_stream(self, filename: str, stream: Stream, *, min_length=None, max_length=None):
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r') -> Stream:
        raise NotImplementedError()

    def locate(self, attachment: 'Attachment') -> str:
        raise NotImplementedError()