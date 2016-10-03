

from sqlalchemy_media.attachments.file import File
from sqlalchemy_media.constants import MB, KB


class Image(File):
    __directory__ = 'images'
    __prefix__ = 'image'

    __max_length__ = 2 * MB
    __min_length__ = 4 * KB
