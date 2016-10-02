
import mimetypes

from sqlalchemy_media.descriptors.stream import CloserStreamDescriptor


class LocalFileSystemDescriptor(CloserStreamDescriptor):

    def __init__(self, filename: str, content_type: str=None, extension: str=None, **kwargs):
        self.original_filename = filename
        if content_type is None:
            content_type = mimetypes.guess_type(filename)[0]

        super().__init__(open(filename, 'rb'), content_type=content_type, **kwargs)

