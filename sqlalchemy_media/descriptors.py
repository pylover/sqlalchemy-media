
import io
from sqlalchemy_media.mimetypes_ import guess_extension, guess_type
from os.path import splitext
from urllib.request import urlopen
from cgi import FieldStorage
from tempfile import TemporaryFile, NamedTemporaryFile

from sqlalchemy_media.typing_ import FileLike, Attachable
from sqlalchemy_media.helpers import is_uri, copy_stream
from sqlalchemy_media.exceptions import MaximumLengthIsReachedError, MinimumLengthIsNotReachedError, \
    DescriptorOperationError


class BaseDescriptor(object):
    """
    Abstract base class for all descriptors. Instance of this class is a file-like object.

    Descriptors are used to get some primitive information from an attachable(file-like object, filename or URI) and
    also allow seeking over underlying file-object. users may not be using this class directly.

    .. seealso:: :class:`.AttachableDescriptor` to know how to use it.

    .. versionadded:: 0.5.0

       - ``min_length`` argument

    :param min_length: Maximum allowed file size.
    :param max_length: Maximum allowed file size.
    :param content_type: The file's mimetype to suppress the mimetype detection.
    :param content_length: The length of the file in bytes, if available. Some descriptors like :class:`.UrlDescriptor`
                           are providing this keyword argument.
    :param extension: The file's extension to suppress guessing it.
    :param original_filename: Original filename, useful to detect `content_type` and or `extension`.
    :param kwargs: Additional keyword arguments to set as attribute on descriptor instance.
    :param header_buffer_size: Amount of bytes to read and buffer from underlying file-like object for analysis purpose
                               if file-like object is not seekable.

    """

    #: Buffer to store cached header on non-seekable file-like objects.
    header = None

    #: Original filename of the underlying file-object.
    original_filename = None

    #: Extension of the underlying file-object.
    extension = None

    #: Content type of the underlying file-object.
    content_type = None

    #: Amount of bytes to cache from header on non-seekable file-like objects.
    header_buffer_size = 1024

    def __init__(self, min_length: int=None, max_length: int=None, content_type: str=None, content_length: int=None,
                 extension: str=None, original_filename: str=None, header_buffer_size=1024, **kwargs):

        self.min_length = min_length
        self.max_length = max_length
        self.header_buffer_size = header_buffer_size
        self.content_length = content_length

        self.original_filename = original_filename

        self._source_pos = 0

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

    def _read_chunked(self, size: int) -> bytes:
        source_cursor = self.tell_source()
        if self.seekable() or self.header is None:
            result = self.read_source(size)
        else:
            current_cursor = self.header.tell()
            cursor_after_read = current_cursor + size

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

    def read(self, size: int=None) -> bytes:
        """
        Read from the underlying file.

        :param size: Amount of bytes ro read.
        """
        if size is None:
            buffer = io.BytesIO()
            copy_stream(self, buffer)
            return buffer.getvalue()
        else:
            return self._read_chunked(size)

    def tell(self) -> int:
        """
        Get the current position of the file-like object. Even if the underlying file-object is not :meth:`.seekable`,
        this method should return the current position which counted internally.
        
        """
        source_cursor = self.tell_source()
        if self.seekable() or self.header is None:
            return source_cursor

        elif self.header.tell() < self.header_buffer_size:
            return self.header.tell()

        else:
            return source_cursor

    def tell_source(self):
        """
        Returns the underlying file-object's current position. even if the underlying file-object is not
        :meth:`.seekable`.

        """
        if self.seekable():
            return self._tell_source()
        else:
            return self._source_pos

    def read_source(self, size: int) -> bytes:
        """
        Used to read from underlying file-object.

        :param size: Amount of bytes to read.
        """
        result = self._read_source(size)
        if not self.seekable():
            self._source_pos += len(result)
        return result

    def get_header_buffer(self) -> bytes:
        """
        Returns the amount of :attr:`.header_buffer_size` from the beginning of the underlying file-object. this method
        should be called many times before the :meth:`.read` method is called on non-seekable descriptors.

        .. warning:: The :exc:`.DescriptorOperationError` will be raised if this method is called after calling the
                     :meth:`.read`. This situation is only happened on non-seekable descriptors.

        .. seealso:: :meth:`.seekable`

        """

        if self.seekable():
            # Preserve the current position:
            pos = self.tell_source()

            # Moving to first byte
            self.seek(0)

            # Reading from header
            buffer = self.read_source(self.header_buffer_size)

            # Seeking back to preserved position
            self.seek(pos)

        elif self.header is None:
            pos = self.tell_source()
            if pos:
                raise DescriptorOperationError(
                    "it's too late to get header buffer from the descriptor. the underlying file-object is not "
                    "seekable and %d bytes are already fetched from." % pos)

            buffer = self.read_source(self.header_buffer_size)
            self.header = io.BytesIO(buffer)
        else:
            buffer = self.header.getvalue()

        return buffer

    def close(self) -> None:
        """
        Closes the underlying file-object. and check for ``min_length``.

        """
        pos = self.tell()
        if self.min_length and self.min_length > pos:
            raise MinimumLengthIsNotReachedError(self.min_length)

    def seekable(self) -> bool:
        """
        **[Abstract]**

        Should be overridden in inherited class and return :data:`True` if the underlying file-object is seekable.

        """
        raise NotImplementedError()  # pragma: no cover

    def _tell_source(self) -> int:
        """
        **[Abstract]**

        Should be overridden in inherited class and return the underlying file-object's current position.
        
        """
        raise NotImplementedError()  # pragma: no cover

    def _read_source(self, size: int) -> bytes:
        """
        **[Abstract]**

        Should be overridden in inherited class and read from underlying file-object.

        :param size: Amount of bytes to read.

        """
        raise NotImplementedError()  # pragma: no cover

    def seek(self, position: int) -> None:
        """
        Seek the file at the given position.

        .. note:: The :exc:`io.UnsupportedOperation` will be raised if the underlying file-object is not
        :meth:`.seekable`.

        :param position: the position to seek on.
        
        """
        raise NotImplementedError('Seek operation is not supported by this object: %r' % self)  # pragma: no cover


class StreamDescriptor(BaseDescriptor):
    """
    This class is used for describing a file-like object. so it's just a proxy for file-like objects.
    The underlying file-object is not meant to be closed after calling the :meth:`.close` method.

    :param stream: File-like object to wrap.
    :param kwargs: the same as the :class:`.BaseDescriptor`
    
    """

    def __init__(self, stream: FileLike, **kwargs):
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
        We are not closing the file-like object here, because we've not opened it.

        """
        super().close()

    @property
    def filename(self):
        """
        Retrieve the filename of the backend file-like object is available.

        """
        if hasattr(self._file, 'name'):
            return self._file.name

        raise DescriptorOperationError('This property is not available on the underlying file-object: %r' % self._file)

    def prepare_to_read(self, backend: str= 'temp') -> None:
        """

        .. versionadded:: 0.5.0

        If the underlying file-object is not seekable, tries to store the underlying non-seekable file-like object as an
        instance of :class:`io.BytesIO`, :obj:`tempfile.NamedTemporaryFile` and :obj:`tempfile.TemporaryFile`.

        .. warning:: Anyway, this method will seeks the descriptor to ``0``.

        .. warning:: If any physical file is created during this operation, This will be deleted after the
                     :meth:`.close` has been called.

        .. warning:: :exc:`.DescriptorOperationError` may be raised, if the current position is greater than zero ``0``,
                     and also if called on a seekable instance.

        .. note:: The ``file`` option is also a temp file but file is guaranteed to have a visible name in the file
                  system (on Unix, the directory entry is not unlinked). filename will be
                  retrieved by the :attr:`.filename`.

        :param backend: Available choices are: ``memory``, ``file`` and ``temp``.

        """

        if self.seekable():
            self.seek(0)
            return

        if backend == 'memory':
            buffer = io.BytesIO()
        elif backend == 'temp':
            buffer = TemporaryFile()
        elif backend == 'file':
            buffer = NamedTemporaryFile()
        else:
            raise DescriptorOperationError('Invalid backend for descriptor: %r' % backend)

        length = copy_stream(self, buffer)
        buffer.seek(0)
        self.replace(
            buffer,
            position=0,
            content_length=length,
            extension=self.extension,
            original_filename=self.original_filename,
        )

    def replace(self, attachable: [io.BytesIO, io.FileIO], position=None, **kwargs):
        """

        .. versionadded:: 0.5.0

        Replace the underlying file-object with a seekable one.

        :param attachable: A seekable file-object.
        :param position: Position of the new seekable file-object. if :data:`.None`, position will be preserved.
        :param kwargs: the same as the :class:`.BaseDescriptor`
        """

        if position is None:
            position = self.tell()
        # Close the old file-like object
        self.close()
        self._file = attachable

        # Some hacks are here:
        super().__init__(**kwargs)
        self.seek(position)


class StreamCloserDescriptor(StreamDescriptor):
    """
    The same as the :class:`.StreamDescriptor`, the only difference is that this class tries to close the file-like
    object after calling the :meth:`.close` method.
    
    """

    def close(self) -> None:
        """
        Overridden to close the underlying file-object.
        
        """
        super().close()
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

    :param storage: The :class:`cgi.FieldStorage` instance to be described.
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

        if isinstance(attachable, FieldStorage):
            return_type = CgiFieldStorageDescriptor
        elif isinstance(attachable, str):
            return_type = UrlDescriptor if is_uri(attachable) else LocalFileSystemDescriptor
        else:
            return_type = StreamDescriptor

        return return_type(attachable, **kwargs)
