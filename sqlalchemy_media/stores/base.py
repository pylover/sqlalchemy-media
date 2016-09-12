
from typing import Union, BinaryIO

from sqlalchemy_media.helpers import open_stream


class Store(object):

    def migrate(self, filename: str, target_store: 'Store') -> int:
        raise NotImplementedError()

    def put(self, filename: str, f: Union[str, BinaryIO]):
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

    def cleanup(self):
        """
        Just do nothing here.
        """
        pass

    def put_stream(self, filename: str, stream: BinaryIO):
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r'):
        raise NotImplementedError()
