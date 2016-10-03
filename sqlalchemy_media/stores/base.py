
from sqlalchemy_media.typing import Stream


class Store(object):
    """
    The abstract base class for all stores.
    """

    # noinspection PyMethodMayBeStatic
    def cleanup(self):
        """
        In derived class should cleanup all dirty stuff created while storing and deleting file.
        If not overridden, no error will be raised.

        .. seealso:: :py:meth:`sqlalchemy_media.stores.StoreManager.cleanup`

        """
        pass

    def put(self, filename: str, stream: Stream, *, min_length=None, max_length=None):
        """
        In driven class, should put the stream as the given filename in the store.

        :param filename:
        :param stream:
        :param min_length:
        :param max_length:
        :return:
        """
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r') -> Stream:
        raise NotImplementedError()

    def locate(self, attachment: 'Attachment') -> str:
        raise NotImplementedError()