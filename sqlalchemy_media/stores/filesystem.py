from typing import BinaryIO

from sqlalchemy_media.stores.base import Store
from sqlalchemy_media.helpers import copy_stream


class FileSystemStore(Store):

    def __init__(self, root_path: str, chunk_size=32768):
        self.root_path = root_path
        self.chunk_size = chunk_size

    def put_stream(self, filename: str, stream: BinaryIO):
        with open(filename, mode='wb') as target_file:
            length = copy_stream(stream, target_file, self.chunk_size)



