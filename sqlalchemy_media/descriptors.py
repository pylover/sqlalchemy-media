
import io
from sqlalchemy_media.mimetypes_ import guess_extension, guess_type
from os.path import splitext
from urllib.request import urlopen
from cgi import FieldStorage

from sqlalchemy_media.typing import Stream, Attachable
from sqlalchemy_media.helpers import is_uri
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError


class BaseDescriptor(object):
    __header_buffer_size__ = 1024
    header = None
    original_filename = None
    extension = None
    content_type = None

    def __init__(self, max_length: int=None, content_type: str=None, content_length: int=None, extension: str=None,
                 original_filename: str=None, **kwargs):
        self.max_length = max_length
        self.content_length = content_length
        self.original_filename = original_filename
        self._source_pos = 0
        if not self.seekable():
            self.header = io.BytesIO(self.read_source(self.__header_buffer_size__))

        for k, v in kwargs.items():
            setattr(self, k, v)

        if content_type:
            self.content_type = content_type
        elif original_filename:
            self.content_type = guess_type(original_filename)
        elif extension:
            self.content_type = guess_type('a' + extension)

        if extension:
            self.extension = extension
        elif self.content_type:
            self.extension = guess_extension(self.content_type)
        elif self.original_filename:
            self.extension = splitext(self.original_filename)[1]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, size):
        if not self.header:
            return self.read_source(size)

        current_cursor = self.header.tell()
        cursor_after_read = current_cursor + size
        source_cursor = self.tell_source()

        if self.max_length is not None and source_cursor > self.max_length:
            raise MaximumLengthIsReachedError(self.max_length)

        if source_cursor > self.__header_buffer_size__ or current_cursor == self.__header_buffer_size__:
            return self.read_source(size)

        if cursor_after_read > self.__header_buffer_size__:
            # split the read, half from header & half from source
            part1 = self.header.read()
            part2 = self.read_source(size - len(part1))
            return part1 + part2
        return self.header.read(size)

    def tell(self):
        source_cursor = self._tell_source()
        if not self.header:
            return source_cursor

        if source_cursor > self.header.tell():
            return self.header.tell()
        return source_cursor

    def seekable(self):
        raise NotImplementedError()

    def tell_source(self):
        if self.seekable():
            return self._tell_source()
        else:
            return self._source_pos

    def read_source(self, size):
        result = self._read_source(size)
        if not self.seekable():
            self._source_pos += len(result)
        return result

    def _tell_source(self):
        raise NotImplementedError()

    def _read_source(self, size):
        raise NotImplementedError()

    def seek(self, position):
        raise NotImplementedError('Seek operation is not supported by this object: %r' % self)

    def close(self):
        raise NotImplementedError()


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


class LocalFileSystemDescriptor(CloserStreamDescriptor):

    def __init__(self, filename: str, original_filename: str=None, **kwargs):
        if original_filename is None:
            original_filename = filename
        super().__init__(open(filename, 'rb'), original_filename=original_filename, **kwargs)


class UrlDescriptor(CloserStreamDescriptor):
    def __init__(self, uri: str, content_type: str=None, original_filename: str=None, **kwargs):
        response = urlopen(uri)

        if content_type is None and 'Content-Type' in response.headers:
            content_type = response.headers.get('Content-Type')

        if 'Content-Length' in response.headers:
            kwargs['content_length'] = int(response.headers.get('Content-Length'))

        if original_filename is None:
            original_filename = uri

        super().__init__(response, content_type=content_type, original_filename=original_filename, **kwargs)


class CgiFieldStorageDescriptor(CloserStreamDescriptor):

    def __init__(self, storage: FieldStorage, content_type: str=None, **kwargs):
        if content_type is None:
            content_type = storage.headers['Content-Type']

        super().__init__(storage.file, content_type=content_type, original_filename=storage.filename, **kwargs)


# noinspection PyAbstractClass
class AttachableDescriptor(BaseDescriptor):

    # noinspection PyInitNewSignature
    def __new__(cls, attachable: Attachable, *args, **kwargs):
        """
        Should determine the appropriate descriptor and return an instance of it.
        :param attachable:
        :param args:
        :param kwargs:
        :return:
        """

        if isinstance(attachable, FieldStorage):
            return_type = CgiFieldStorageDescriptor
        elif isinstance(attachable, str):
            return_type = UrlDescriptor if is_uri(attachable) else LocalFileSystemDescriptor
        else:
            return_type = StreamDescriptor

        return return_type(attachable, *args, **kwargs)
