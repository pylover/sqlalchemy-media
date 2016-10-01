
from sqlalchemy_media.typing import Stream


class Store(object):

    # noinspection PyMethodMayBeStatic
    def cleanup(self):
        """
        Just do nothing here.
        """
        pass

    def put(self, filename: str, stream: Stream, *, min_length=None, max_length=None):
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r') -> Stream:
        raise NotImplementedError()

    def locate(self, attachment: 'Attachment') -> str:
        raise NotImplementedError()