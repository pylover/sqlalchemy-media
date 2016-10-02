
from sqlalchemy_media.descriptors.stream import CloserStreamDescriptor


class LocalFileSystemDescriptor(CloserStreamDescriptor):

    def __init__(self, filename: str, original_filename: str=None, **kwargs):
        if original_filename is None:
            original_filename = filename
        super().__init__(open(filename, 'rb'), original_filename=original_filename, **kwargs)

