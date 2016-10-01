
from cgi import FieldStorage

from sqlalchemy_media.descriptors.stream import CloserStreamDescriptor


class CgiFieldStorageDescriptor(CloserStreamDescriptor):

    def __init__(self, storage: FieldStorage, content_type: str=None, **kwargs):
        self.original_filename = storage.filename
        if content_type is None:
            content_type = storage.headers['Content-Type']

        super().__init__(storage.file, content_type=content_type, **kwargs)
