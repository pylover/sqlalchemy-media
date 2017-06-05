
from os import makedirs, remove
from os.path import abspath, join, dirname, exists

from sqlalchemy_media.helpers import copy_stream
from sqlalchemy_media.typing_ import FileLike
from .base import Store


class FileSystemStore(Store):
    """
    Store for dealing with local file-system.

    :param root_path: The path to a directory to store files.
    :param base_url: The base url path to include at the beginning of the file's path to yield the access url.
    :param chunk_size: Length of the chunks to read/write from/to files. default: 32768
    """

    def __init__(self, root_path: str, base_url: str, chunk_size: int=32768):
        self.root_path = abspath(root_path)
        self.base_url = base_url.rstrip('/')
        self.chunk_size = chunk_size

    def _get_physical_path(self, filename: str) -> str:
        return join(self.root_path, filename)

    def put(self, filename: str, stream: FileLike):
        physical_path = self._get_physical_path(filename)
        physical_directory = dirname(physical_path)

        if not exists(physical_directory):
            makedirs(physical_directory, exist_ok=True)

        with open(physical_path, mode='wb') as target_file:
            return copy_stream(
                stream,
                target_file,
                chunk_size=self.chunk_size
            )

    def delete(self, filename: str):
        physical_path = self._get_physical_path(filename)
        remove(physical_path)

    def open(self, filename: str, mode: str='rb') -> FileLike:
        return open(self._get_physical_path(filename), mode=mode)

    def locate(self, attachment) -> str:
        return '%s/%s' % (self.base_url, attachment.path)