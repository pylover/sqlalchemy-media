

from sqlalchemy_media.typing import Stream
from sqlalchemy_media.descriptors.base import BaseDescriptor


class StreamDescriptor(BaseDescriptor):

    def __init__(self, stream: Stream, **kwargs):
        self._file = stream
        super().__init__(**kwargs)

    def _tell_source(self) -> int:
        return self._file.tell()

    def _read_source(self, size: int) -> bytes:
        return self._file.read(size)

    def seek(self, position: int):
        self._file.seek(position)

    def seekable(self):
        return self._file.seekable()

    def close(self) -> None:
        """
        Do not closing the stream here, because we'r not upened it.
        :return:
        """
        pass


class CloserStreamDescriptor(StreamDescriptor):

    def close(self) -> None:
        self._file.close()
