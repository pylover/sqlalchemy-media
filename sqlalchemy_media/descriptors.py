
import io
from sqlalchemy_media.mimetypes_ import guess_extension, guess_type
from os.path import splitext
from urllib.request import urlopen
from cgi import FieldStorage

from sqlalchemy_media.typing_ import Stream, Attachable
from sqlalchemy_media.helpers import is_uri
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError


class BaseDescriptor(object):
    """
    Abstract base class for all descriptors. Instance of this class is a file-like object.

    Descriptors are used to get some primitive information from an attachable(stream, filename or URI). users may not using this class directly. see :class:`.AttachableDescriptor` to see usage.

    :param max_length: Maximum allowed file size.
    :param content_type: The file's mimetype to suppress the mimetype detection.
    :param content_length: The length of file in bytes, if available. Some descriptors like :class:`.UrlDescriptor`
                           are providing this keyword argument.
    :param extension: The file's extension to suppress guessing it.
    :param original_filename: Original filename, useful to detect `content_type` and or `extension`.
    :param kwargs: Additional keyword arguments to set as attribute on descriptor instance.
    :param header_buffer_size: Amount of bytes to read and buffer from stream for analysis purpose if stream is not
                               seekable.

    """

    header = None
    original_filename = None
    extension = None
    content_type = None

    def __init__(self, max_length: int=None, content_type: str=None, content_length: int=None, extension: str=None,
                 original_filename: str=None, header_buffer_size=1024, **kwargs):

        self.max_length = max_length
        self.header_buffer_size = header_buffer_size
        self.content_length = content_length
        self.original_filename = original_filename
        self._source_pos = 0
        if not self.seekable():
            self.header = io.BytesIO(self.read_source(self.header_buffer_size))

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
        elif self.original_filename:
            self.extension = splitext(self.original_filename)[1]
        elif self.content_type:
            self.extension = guess_extension(self.content_type)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, size: int) -> bytes:
        """
        Read from the underlying file.

        :param size: Amount of bytes ro read.
        """
        if not self.header:
            return self.read_source(size)

        current_cursor = self.header.tell()
        cursor_after_read = current_cursor + size
        source_cursor = self.tell_source()

        if self.max_length is not None and source_cursor > self.max_length:
            raise MaximumLengthIsReachedError(self.max_length)

        elif source_cursor > self.header_buffer_size or current_cursor == self.header_buffer_size:
            result = self.read_source(size)

        elif cursor_after_read > self.header_buffer_size:
            # split the read, half from header & half from source
            part1 = self.header.read()
            part2 = self.read_source(size - len(part1))
            result = part1 + part2
        else:
            result = self.header.read(size)

        if self.max_length is not None and source_cursor + len(result) > self.max_length:
            raise MaximumLengthIsReachedError(self.max_length)

        return result

    def tell(self) -> int:
        """
        Get the current position of the stream. Even if the underlying stream is not :meth:`.seekable`, this method
        should return the current position which counted internally.
        """
        source_cursor = self.tell_source()
        if not self.header:
            return source_cursor

        elif self.header.tell() < self.header_buffer_size:
            return self.header.tell()

        else:
            return source_cursor

    def tell_source(self):
        """
        Returns the underlying stream's current position. even if the underlying stream is not :meth:`.seekable`.

        """
        if self.seekable():
            return self._tell_source()
        else:
            return self._source_pos

    def read_source(self, size: int) -> bytes:
        """
        Used to read from underlying stream.

        :param size: Amount of bytes to read.
        """
        result = self._read_source(size)
        if not self.seekable():
            self._source_pos += len(result)
        return result

    def seekable(self) -> bool:
        """
        **[Abstract]**

        Should be overridden in inherited class and return :data:`True` if the underlying stream is seekable.

        """
        raise NotImplementedError()  # pragma: no cover

    def _tell_source(self) -> int:
        """
        **[Abstract]**

        Should be overridden in inherited class and return the underlying stream's current position.
        """
        raise NotImplementedError()  # pragma: no cover

    def _read_source(self, size: int) -> bytes:
        """
        **[Abstract]**

        Should be overridden in inherited class and read from underlying stream.

        :param size: Amount of bytes to read.

        """
        raise NotImplementedError()  # pragma: no cover

    def seek(self, position: int) -> None:
        """
        Seek the file at the given position.

        .. note:: The :exc:`io.UnsupportedOperation` will be raised if the underlying stream is not :meth:`.seekable`.

        :param position: the position to seek on.
        """
        raise NotImplementedError('Seek operation is not supported by this object: %r' % self)  # pragma: no cover

    def close(self) -> None:
        """
        Closes the underlying stream.
        """
        raise NotImplementedError()  # pragma: no cover


class StreamDescriptor(BaseDescriptor):
    """
    This class is used for describing a stream. so it just a proxy for streams.
    The underlying stream will not to be closed after calling the :meth:`.close` method.

    :param stream: File-like object to wrap.
    :param kwargs: the same as the :class:`.BaseDescriptor`
    """

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
        Do not closing the stream here, because we'r not opened it.

        """
        pass


class StreamCloserDescriptor(StreamDescriptor):
    """
    The same as the :class:`.StreamDescriptor`, the only difference is this class trying to close the stream after
    calling the :meth:`.close` method.
    """

    def close(self) -> None:
        """
        Overridden to close the underlying stream.
        """
        self._file.close()


class LocalFileSystemDescriptor(StreamCloserDescriptor):
    """
    Representing a file on the local file system.

    :param filename: The filename on the local storage to open for reading.
    :param kwargs: the same as the :class:`.BaseDescriptor`

    .. note:: the `filename` will be passed as `original_filename` to the parent class.

    """

    def __init__(self, filename: str, original_filename: str=None, **kwargs):
        if original_filename is None:
            original_filename = filename
        super().__init__(open(filename, 'rb'), original_filename=original_filename, **kwargs)


class UrlDescriptor(StreamCloserDescriptor):
    """
    Open a remote resource with :mod:`urllib` and pass the `content_type` and `content_length` to the parent class.

    :param uri: The uri to open.
    :param kwargs: the same as the :class:`.BaseDescriptor`

    .. note:: the `uri` will be passed as `original_filename` to the parent class, if the `original_filename` is
              :data:`None`.

    """

    def __init__(self, uri: str, content_type: str=None, original_filename: str=None, **kwargs):
        response = urlopen(uri)

        if content_type is None and 'Content-Type' in response.headers:
            content_type = response.headers.get('Content-Type')

        if 'Content-Length' in response.headers:
            kwargs['content_length'] = int(response.headers.get('Content-Length'))

        if original_filename is None:
            original_filename = uri

        super().__init__(response, content_type=content_type, original_filename=original_filename, **kwargs)


class CgiFieldStorageDescriptor(StreamCloserDescriptor):
    """
    Describes a :class:`cgi.FieldStorage`.

    :param storage: The :class:`cgi.FieldStorage` instance to describe.
    :param kwargs: the same as the :class:`.BaseDescriptor`

    """

    def __init__(self, storage: FieldStorage, content_type: str=None, **kwargs):
        if content_type is None:
            content_type = storage.headers['Content-Type']

        super().__init__(storage.file, content_type=content_type, original_filename=storage.filename, **kwargs)


# noinspection PyAbstractClass
class AttachableDescriptor(BaseDescriptor):
    """

    This is an abstract factory for descriptors based on the first argument

    .. doctest::

        >>> from sqlalchemy_media import AttachableDescriptor
        >>> with AttachableDescriptor('index.rst') as descriptor:
        ...     print(type(descriptor))
        <class 'sqlalchemy_media.descriptors.LocalFileSystemDescriptor'>

    So this callable, should determine the appropriate descriptor and return an instance of it.

    :param attachable: filename, uri or file-like object
    :param kwargs: the same as the :class:`.BaseDescriptor`

    """

    # noinspection PyInitNewSignature
    def __new__(cls, attachable: Attachable, **kwargs):
        """

        :return:
        """

        if isinstance(attachable, FieldStorage):
            return_type = CgiFieldStorageDescriptor
        elif isinstance(attachable, str):
            return_type = UrlDescriptor if is_uri(attachable) else LocalFileSystemDescriptor
        else:
            return_type = StreamDescriptor

        return return_type(attachable, **kwargs)
