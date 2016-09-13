
from typing import Union, IO
from io import BytesIO


from sqlalchemy_media.helpers import open_stream


Stream = Union[IO[BytesIO], BytesIO]


class Store(object):

    def migrate(self, filename: str, target_store: 'Store') -> int:
        raise NotImplementedError()

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

    def cleanup(self):
        """
        Just do nothing here.
        """
        pass

    def put_stream(self, filename: str, stream: Stream):
        raise NotImplementedError()

    def delete(self, filename: str):
        raise NotImplementedError()

    def open(self, filename: str, mode: str='r'):
        raise NotImplementedError()
